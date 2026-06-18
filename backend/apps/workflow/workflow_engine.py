# -*- coding: utf-8 -*-
"""工作流执行引擎
========================================================
WorkflowEngine：从 FusionPipelinePack + FusionPipelineNode 读取编排配置，
按依赖关系调度执行，并写入 WorkflowInstance / NodeExecution 作为执行轨迹。

架构要点：
  ① 执行计划构建：以 upstream_deps 为主，chain_order 作为回退排序，
     保证新旧模板都能跑
  ② 节点执行：每个节点独立的 NodeExecution，含重试/超时/计费
  ③ 状态机：严格在 running/paused/failed/done 之间转移
  ④ 可插拔 runner：通过 SkillBridge 路由：
       - skill_id 命中 → SkillInvoker.invoke()  （新引擎唯一主路径）
       - runner_path 兜底 → Python 函数         （仅供非默认 pack 的自定义节点）

节点 runner 类型与映射：
  fusion_node     → 标准创作节点（SkillInvoker → creation.{brief,structure,...}）
  parallel_group  → 并行组（P1 扩展）
  iterate_loop    → 循环节点（P1 扩展）
  human_gate      → 人工门控（P1 扩展）
========================================================
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from django.utils import timezone

from apps.workflow.condition_evaluator import eval_node_condition
from apps.workflow.execution_models import NodeExecution, WorkflowInstance
from apps.workflow.runtime_contract import (
    compress_context_for_storage,
    node_input_snapshot,
    project_seed_context,
    record_execution_event,
)


logger = logging.getLogger(__name__)


# =========================================================
# 节点配置 — 统一抽象（屏蔽数据库层细节）
# =========================================================
@dataclass
class NodeConfig:
    """引擎内部的节点配置快照（从 FusionPipelineNode 解包）。"""
    node_id: str             # fusion_node_id
    name: str
    runner_type: str         # fusion_node / parallel_group / ...
    chain_order: int
    website_index: int = 0
    skill_id: str = ""       # 技能 ID（SkillBridge 路由用）
    runner_path: str = ""    # Python 函数路径（SkillBridge 路由用）
    upstream_deps: List[str] = field(default_factory=list)
    downstream_map: List[Dict[str, Any]] = field(default_factory=list)
    runtime_config: Dict[str, Any] = field(default_factory=dict)
    condition_expr: str = ""
    extra_config: Dict[str, Any] = field(default_factory=dict)
    coin_cost: int = 10

    # ── 从 runtime_config 读取便捷字段 ──
    @property
    def timeout_seconds(self) -> int:
        return int(self.runtime_config.get("timeout_seconds", 600))

    @property
    def max_retries(self) -> int:
        return int(self.runtime_config.get("retry_policy", {}).get("max_retries", 3))

    @property
    def backoff_base(self) -> float:
        return float(self.runtime_config.get("retry_policy", {}).get("base_seconds", 2))

    @property
    def backoff_strategy(self) -> str:
        return self.runtime_config.get("retry_policy", {}).get("backoff", "exponential")

    @property
    def allow_skip_on_failure(self) -> bool:
        return bool(self.runtime_config.get("allow_skip", False))

    @property
    def is_checkpoint(self) -> bool:
        return bool(self.runtime_config.get("is_checkpoint", False))

    @property
    def human_gate_required(self) -> bool:
        return bool(self.runtime_config.get("human_gate_required", False))

    @property
    def max_context_bytes(self) -> int:
        return int(self.runtime_config.get("max_context_bytes", 2 * 1024 * 1024))


# =========================================================
# 执行结果（供引擎内部使用）
# =========================================================
@dataclass
class NodeRunResult:
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    coin_cost: int = 0
    llm_token_in: int = 0
    llm_token_out: int = 0
    duration_ms: int = 0
    retry_count: int = 0
    was_skipped: bool = False
    was_human_gate: bool = False
    error_code: str = ""

    @classmethod
    def from_agent_result(
        cls,
        agent_result: Any,
        *,
        duration_ms: int,
        retry_count: int = 0,
    ) -> "NodeRunResult":
        """从现有的 AgentResult 转换，保持字段一致。"""
        success = getattr(agent_result, "status", "") == "completed"
        output: Dict[str, Any] = {}
        meta = getattr(agent_result, "meta", None) or {}
        outputs = getattr(agent_result, "outputs", None) or {}

        # 保留现有 fusion 元数据
        if "fusion" in meta:
            output["fusion"] = meta["fusion"]
        # 合并所有输出字段（扁平化，避免嵌套过深）
        if isinstance(outputs, dict):
            for key, value in outputs.items():
                if isinstance(value, (str, int, float, bool, list, dict)):
                    output[key] = value

        return cls(
            success=success,
            output=output,
            errors=list(getattr(agent_result, "errors", None) or []),
            coin_cost=int(outputs.get("coin_cost", 0) or 0),
            llm_token_in=int(outputs.get("llm_token_in", 0) or 0),
            llm_token_out=int(outputs.get("llm_token_out", 0) or 0),
            duration_ms=duration_ms,
            retry_count=retry_count,
        )

    @classmethod
    def skip(cls) -> "NodeRunResult":
        return cls(success=True, was_skipped=True)

    @classmethod
    def human_gate(cls) -> "NodeRunResult":
        return cls(success=True, was_human_gate=True)


# =========================================================
# WorkflowEngine 核心
# =========================================================
class WorkflowEngine:
    """LEGACY — Fusion 工作流执行引擎，独立 Agent 工作台不使用。

    典型用法（Celery 任务中）：
        instance = WorkflowInstance.objects.get(id=instance_id)
        engine = WorkflowEngine(instance, agent_runner=_default_runner)
        engine.run()

    单步调试：
        engine = WorkflowEngine(instance, dry_run=True)
        plan = engine.build_execution_plan(start_node_id="node_brief")
        for step in plan:
            print(step)
    """

    def __init__(
        self,
        instance: WorkflowInstance,
        *,
        agent_runner: Optional[Callable[..., Any]] = None,
        billing_service: Optional[Callable[..., bool]] = None,
        dry_run: bool = False,
    ) -> None:
        self.instance = instance
        self.pack = instance.pack
        self.project = instance.project
        self.dry_run = dry_run

        # 外部依赖注入（便于测试 mock）
        self._agent_runner = agent_runner or _default_agent_runner
        self._billing = billing_service or _default_billing_ok

        # 运行时内部状态
        self._nodes_by_id: Dict[str, NodeConfig] = self._load_node_configs()
        self._completed_outputs: Dict[str, Dict[str, Any]] = {}
        self._last_output: Optional[Dict[str, Any]] = None
        self._heartbeat_interval_seconds = int(
            (self.pack.engine_config or {}).get("heartbeat_interval_seconds", 60)
        )
        self._last_heartbeat = 0.0

    # ─────────────────────────────────────────
    # 步骤 0：加载节点配置
    # ─────────────────────────────────────────
    def _load_node_configs(self) -> Dict[str, NodeConfig]:
        """从 pack.nodes 关联表构建 NodeConfig 索引。"""
        from apps.workflow.models import FusionPipelineNode

        nodes_qs = FusionPipelineNode.objects.filter(
            pack=self.pack, enabled=True
        ).order_by("chain_order")

        result: Dict[str, NodeConfig] = {}
        for db_node in nodes_qs:
            cfg = NodeConfig(
                node_id=db_node.fusion_node_id,
                name=db_node.name,
                runner_type=db_node.runner_type or "fusion_node",
                chain_order=db_node.chain_order,
                website_index=db_node.website_index,
                skill_id=db_node.skill_id or "",
                runner_path=db_node.runner_path or "",
                upstream_deps=list(db_node.upstream_deps or []),
                downstream_map=list(db_node.downstream_map or []),
                runtime_config=dict(db_node.runtime_config or {}),
                condition_expr=db_node.condition_expr or "",
                extra_config=dict(db_node.extra_config or {}),
                coin_cost=int(db_node.coin_cost or 10),
            )
            result[cfg.node_id] = cfg
        return result

    # ─────────────────────────────────────────
    # 步骤 1：构建执行计划（拓扑排序）
    # ─────────────────────────────────────────
    def build_execution_plan(
        self, start_node_id: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        """按依赖关系拓扑排序，返回 [(node_id, reason), ...]。

        策略：
          ① 若任何节点声明了 upstream_deps → 严格按依赖拓扑排序
          ② 否则 → 按 chain_order 线性执行（兼容旧模板）
        """
        node_ids = list(self._nodes_by_id.keys())
        if not node_ids:
            return []

        has_upstream = any(
            bool(n.upstream_deps) for n in self._nodes_by_id.values()
        )

        if not has_upstream:
            # 回退：按 chain_order 线性执行
            ordered = sorted(
                node_ids, key=lambda nid: self._nodes_by_id[nid].chain_order
            )
            if start_node_id and start_node_id in ordered:
                ordered = ordered[ordered.index(start_node_id):]
            return [(nid, "linear_by_chain_order") for nid in ordered]

        # 拓扑排序：按 upstream_deps
        in_degree: Dict[str, int] = {nid: 0 for nid in node_ids}
        adj: Dict[str, List[str]] = {nid: [] for nid in node_ids}

        for nid, cfg in self._nodes_by_id.items():
            for dep in cfg.upstream_deps:
                if dep in in_degree:
                    in_degree[nid] += 1
                    adj[dep].append(nid)

        # BFS
        queue: List[str] = [nid for nid, d in in_degree.items() if d == 0]
        queue.sort(key=lambda nid: self._nodes_by_id[nid].chain_order)
        plan: List[str] = []

        while queue:
            current = queue.pop(0)
            plan.append(current)
            for next_node in adj[current]:
                in_degree[next_node] -= 1
                if in_degree[next_node] == 0:
                    queue.append(next_node)
            queue.sort(key=lambda nid: self._nodes_by_id[nid].chain_order)

        if len(plan) != len(node_ids):
            # 有环，退回到 chain_order 并告警
            logger.error(
                "[Engine] 检测到依赖环，回退使用 chain_order。pack=%s",
                self.pack.id,
            )
            plan = sorted(
                node_ids, key=lambda nid: self._nodes_by_id[nid].chain_order
            )

        # 截取起始节点
        if start_node_id and start_node_id in plan:
            plan = plan[plan.index(start_node_id):]

        return [(nid, "topological_by_upstream_deps") for nid in plan]

    # ─────────────────────────────────────────
    # 步骤 2：主执行循环
    # ─────────────────────────────────────────
    def run(self, start_node_id: Optional[str] = None) -> WorkflowInstance:
        """执行完整工作流，返回更新后的 instance。"""
        try:
            # 从指定节点启动（断点续跑/局部重跑）
            effective_start = start_node_id or self.instance.start_node_id or None

            # 标记为 running
            self.instance.transition_to(
                "running",
                reason="engine_start",
                node_id=effective_start or "",
            )
            self._seed_initial_context()

            plan = self.build_execution_plan(start_node_id=effective_start)
            logger.info(
                "[Engine] pack=%s instance=%s plan=%s nodes",
                self.pack.id, self.instance.id, len(plan),
            )

            total = len(plan)
            for idx, (node_id, reason) in enumerate(plan, start=1):
                # 每次循环检查心跳/外部取消
                if self.instance.status != "running":
                    logger.warning(
                        "[Engine] 中断执行：当前状态=%s，期待=running",
                        self.instance.status,
                    )
                    break

                logger.info(
                    "[Engine] 执行节点 %d/%d: %s (%s)",
                    idx, total, node_id, reason,
                )
                self._execute_node(node_id, progress=(idx, total))
                if self.instance.status != "running":
                    break

                # 节点之后：若下游条件路由显式指定了其它节点，则打断默认顺序
                # （由 _decide_next_node 动态覆盖默认 plan，简化实现这里保持顺序）
                # TODO(P1): 支持 downstream_map 动态分支路由

            # 全部完成
            if self.instance.status == "running":
                self.instance.transition_to("done", reason="all_nodes_completed")

        except Exception as exc:
            logger.exception("[Engine] 引擎崩溃: %s", exc)
            self.instance.transition_to(
                "failed",
                reason=f"unhandled_exception:{type(exc).__name__}:{exc}",
            )

        finally:
            # 聚合金币/token统计
            self._aggregate_instance_stats()

        return self.instance

    def _seed_initial_context(self) -> None:
        """Seed project request fields into instance.context once."""
        seed = project_seed_context(self.project)
        if not seed:
            return
        ctx = dict(self.instance.context or {})
        changed = False
        for key, value in seed.items():
            if key not in ctx and value not in (None, ""):
                ctx[key] = value
                changed = True
        if changed:
            self.instance.context = ctx
            self.instance.save(update_fields=["context"])

    # ─────────────────────────────────────────
    # 步骤 3：单节点执行
    # ─────────────────────────────────────────
    def _execute_node(
        self, node_id: str, *, progress: Tuple[int, int]
    ) -> NodeExecution:
        """执行单个节点（含条件判断/重试/超时/上下文更新）。"""
        cfg = self._nodes_by_id.get(node_id)
        if cfg is None:
            logger.error("[Engine] 找不到节点配置: %s", node_id)
            return self._record_failed_execution(
                node_id,
                error="missing_node_config",
                error_code="config_missing",
            )

        # 心跳
        self._heartbeat()

        # 创建 NodeExecution（pending）
        exec_rec = NodeExecution.objects.create(
            instance=self.instance,
            node_id=node_id,
            node_name=cfg.name,
            runner_type=cfg.runner_type,
            idempotency_key=f"{self.instance.id}:{node_id}:{uuid.uuid4().hex[:8]}",
        )
        exec_rec.mark_running(
            input_context=node_input_snapshot(self.instance.context or {}, cfg)
        )
        record_execution_event(
            exec_rec,
            "node_start",
            message=f"start {node_id}",
            extra={
                "progress": {"index": progress[0], "total": progress[1]},
                "skill_id": cfg.skill_id,
                "runner_type": cfg.runner_type,
            },
        )
        self.instance.current_node_id = node_id
        self.instance.save(update_fields=["current_node_id"])

        # ① 条件判断
        if cfg.condition_expr:
            ok, err_msg = eval_node_condition(
                cfg.condition_expr,
                instance_context=self.instance.context or {},
                last_node_output=self._last_output,
                completed_nodes_outputs=self._completed_outputs,
                pack_constants=(self.pack.engine_config or {}).get("constants"),
            )
            if not ok:
                logger.info(
                    "[Engine] 节点 %s 条件不满足，跳过。expr=%s error=%s",
                    node_id, cfg.condition_expr, err_msg,
                )
                exec_rec.mark_skipped(
                    reason=f"condition_false:{cfg.condition_expr}" +
                    (f"({err_msg})" if err_msg else ""),
                )
                return exec_rec

        # ② 人工门控（需要运营或用户确认）
        if cfg.human_gate_required or cfg.runner_type == "human_gate":
            logger.info("[Engine] 节点 %s 需人工确认，挂起实例", node_id)
            self.instance.transition_to(
                "waiting_human", reason="human_gate_required", node_id=node_id,
            )
            exec_rec.status = "pending"
            exec_rec.save(update_fields=["status"])
            return exec_rec

        # ③ 节点执行（带重试/超时）
        try:
            result = self._run_node_with_retries(cfg, exec_rec)
        except Exception as exc:
            logger.exception("[Engine] 节点 %s 执行异常", node_id)
            exec_rec.mark_failed(
                error=str(exc),
                error_code="node_run_exception",
                coin_cost=cfg.coin_cost,
            )
            # 是否允许跳过
            if cfg.allow_skip_on_failure:
                logger.warning(
                    "[Engine] 节点 %s 失败但 allow_skip=true，继续执行", node_id,
                )
                return exec_rec
            self.instance.transition_to(
                "failed", reason=f"node_failed:{node_id}", node_id=node_id,
            )
            return exec_rec

        # ④ 成功 → 写回上下文
        if result.success and not result.was_skipped:
            exec_rec.mark_success(
                output_context=result.output,
                coin_cost=result.coin_cost,
                llm_token_in=result.llm_token_in,
                llm_token_out=result.llm_token_out,
            )
            # 写回全局上下文（仅当节点是检查点，或输出有明确 artifact_key）
            self._write_node_output_to_context(cfg, result.output)
            self._last_output = result.output
            self._completed_outputs[node_id] = result.output
        elif result.was_skipped:
            exec_rec.mark_skipped(reason="upstream_or_runtime_skip")
        else:
            error_msg = "; ".join(result.errors or ["node failed"])
            exec_rec.mark_failed(
                error=error_msg,
                error_code=result.error_code or "node_failed",
                coin_cost=result.coin_cost,
            )
            record_execution_event(
                exec_rec,
                "node_failed",
                level="error",
                message=error_msg[:500],
                extra={"errors": result.errors, "retry_count": result.retry_count},
            )
            if not cfg.allow_skip_on_failure:
                self.instance.transition_to(
                    "failed", reason=f"node_failed:{node_id}:{error_msg[:200]}", node_id=node_id,
                )

        return exec_rec

    # ─────────────────────────────────────────
    # 步骤 4：节点重试/超时逻辑
    # ─────────────────────────────────────────
    def _run_node_with_retries(
        self, cfg: NodeConfig, exec_rec: NodeExecution
    ) -> NodeRunResult:
        """封装重试/退避/累加/回补逻辑。

        P2 阶段增强：
          • 每轮重试都累计 coin_cost / llm_token_in / llm_token_out
          • 最终失败时调用 refund_coins 回补失败前扣的金币
          • 把 retry_count 写入 NodeExecution
          • 退避策略由 cfg.backoff_strategy (exponential/linear/fixed) 控制
        """
        last_error: Optional[Exception] = None
        last_result: Optional[NodeRunResult] = None
        attempts_done = 0

        # 累加器：贯穿所有重试
        total_coin_cost = 0
        total_token_in = 0
        total_token_out = 0

        for attempt in range(cfg.max_retries + 1):
            attempts_done = attempt
            # 心跳（防止长时间任务被 watchdog 误判为挂起）
            self._heartbeat()

            t0 = time.monotonic()
            try:
                # 调用实际 agent runner
                agent_result = self._agent_runner(
                    project=self.project,
                    node_config=cfg,
                    context=self.instance.context or {},
                    dry_run=self.dry_run,
                )
                duration = int((time.monotonic() - t0) * 1000)

                result = NodeRunResult.from_agent_result(
                    agent_result,
                    duration_ms=duration,
                    retry_count=attempt,
                )

                # 累加每次成本（成功或失败均累加）
                total_coin_cost += result.coin_cost
                total_token_in += result.llm_token_in
                total_token_out += result.llm_token_out

                if result.success:
                    logger.info(
                        "[Engine] 节点 %s 成功（attempt=%d/%d，耗时 %dms，累计金币 %d）",
                        cfg.node_id, attempt + 1, cfg.max_retries + 1,
                        duration, total_coin_cost,
                    )
                    # 把累计成本回填到 result 以便持久化
                    result.coin_cost = total_coin_cost
                    result.llm_token_in = total_token_in
                    result.llm_token_out = total_token_out
                    # 同步写入 NodeExecution 的 retry_count
                    exec_rec.retry_count = attempt
                    exec_rec.save(update_fields=["retry_count", "updated_at"])
                    record_execution_event(
                        exec_rec,
                        "attempt_success",
                        duration_ms=duration,
                        extra={
                            "attempt": attempt + 1,
                            "coin_cost": result.coin_cost,
                            "llm_token_in": result.llm_token_in,
                            "llm_token_out": result.llm_token_out,
                        },
                    )
                    return result

                last_result = result
                last_error = RuntimeError(result.errors[-1] if result.errors else "unknown")
                record_execution_event(
                    exec_rec,
                    "attempt_failed",
                    level="warn",
                    duration_ms=duration,
                    message=str(last_error)[:500],
                    extra={"attempt": attempt + 1, "errors": result.errors},
                )

            except Exception as exc:
                duration = int((time.monotonic() - t0) * 1000)
                logger.warning(
                    "[Engine] 节点 %s 第 %d 次尝试失败: %s",
                    cfg.node_id, attempt + 1, exc,
                )
                last_error = exc
                record_execution_event(
                    exec_rec,
                    "attempt_exception",
                    level="warn",
                    duration_ms=duration,
                    message=str(exc)[:500],
                    extra={"attempt": attempt + 1, "exception_type": type(exc).__name__},
                )

            # 失败重试退避
            if attempt < cfg.max_retries:
                sleep_sec = self._compute_backoff(cfg, attempt)
                logger.info(
                    "[Engine] 节点 %s %ds 后重试（%d/%d）",
                    cfg.node_id, sleep_sec, attempt + 2, cfg.max_retries + 1,
                )
                time.sleep(sleep_sec)

        # 全部尝试失败 → 触发配额回补
        exec_rec.retry_count = attempts_done
        if total_coin_cost > 0 and self.instance.user_id:
            self._refund_node_quota(
                cfg=cfg, exec_rec=exec_rec, amount=total_coin_cost,
            )
        exec_rec.save(update_fields=["retry_count", "updated_at"])

        if last_result:
            last_result.retry_count = attempts_done
            last_result.coin_cost = total_coin_cost
            last_result.llm_token_in = total_token_in
            last_result.llm_token_out = total_token_out
            return last_result
        return NodeRunResult(
            success=False,
            errors=[f"{type(last_error).__name__}:{last_error}" if last_error else "unknown"],
            retry_count=attempts_done,
            coin_cost=total_coin_cost,
            llm_token_in=total_token_in,
            llm_token_out=total_token_out,
            error_code="max_retries_exceeded",
        )

    def _refund_node_quota(
        self, *, cfg: NodeConfig, exec_rec: NodeExecution, amount: int,
    ) -> None:
        """节点最终失败时回补已扣金币。"""
        if amount <= 0:
            return
        try:
            from apps.billing.services import refund_coins

            refund_coins(
                user_id=int(self.instance.user_id),
                amount=amount,
                description=f"节点 {cfg.node_id} 重试后失败，金币回补",
                reference_id=f"wf_node_refund:{exec_rec.idempotency_key}",
            )
            exec_rec.quota_refunded = True
            logger.info(
                "[Engine] 节点 %s 金币 %d 已回补", cfg.node_id, amount,
            )
        except Exception as exc:
            logger.warning(
                "[Engine] 节点 %s 金币回补失败: %s", cfg.node_id, exc,
            )

    @staticmethod
    def _compute_backoff(cfg: NodeConfig, attempt: int) -> float:
        if cfg.backoff_strategy == "fixed":
            return cfg.backoff_base
        if cfg.backoff_strategy == "linear":
            return cfg.backoff_base * (attempt + 1)
        # exponential（默认）
        return cfg.backoff_base * (2 ** attempt)

    # ─────────────────────────────────────────
    # 辅助：写回上下文
    # ─────────────────────────────────────────
    def _write_node_output_to_context(
        self, cfg: NodeConfig, output: Dict[str, Any]
    ) -> None:
        """将节点输出写回 instance.context（仅保留必要字段防膨胀）。"""
        if not output:
            return
        ctx = dict(self.instance.context or {})
        # 1) 优先使用节点自身输出的 artifact_key
        artifact_key = output.get("artifact_key") or cfg.node_id
        # 2) 整份输出写到 ctx.nodes[node_id]
        ctx.setdefault("nodes", {})[cfg.node_id] = output
        # 3) 如有 artifact_key，顶层级联
        if artifact_key:
            ctx[artifact_key] = output.get("content") or output
        ctx, stats = compress_context_for_storage(ctx, cfg)
        if stats.get("level", 0) > 0:
            logger.warning(
                "[Engine] instance.context compressed node=%s from=%s to=%s",
                cfg.node_id, stats.get("bytes_before"), stats.get("bytes_after"),
            )
        self.instance.context = ctx
        self.instance.save(update_fields=["context"])

    # ─────────────────────────────────────────
    # 辅助：失败节点执行记录
    # ─────────────────────────────────────────
    def _record_failed_execution(
        self, node_id: str, *, error: str, error_code: str
    ) -> NodeExecution:
        return NodeExecution.objects.create(
            instance=self.instance,
            node_id=node_id,
            node_name=node_id,
            runner_type="unknown",
            status="failed",
            errors=[{"code": error_code, "message": error[:2000]}],
            idempotency_key=f"{self.instance.id}:{node_id}:fail:{uuid.uuid4().hex[:6]}",
        )

    # ─────────────────────────────────────────
    # 辅助：统计汇总
    # ─────────────────────────────────────────
    def _aggregate_instance_stats(self) -> None:
        qs = NodeExecution.objects.filter(instance=self.instance)
        total_coin = 0
        total_in = 0
        total_out = 0
        for rec in qs.only("coin_cost", "llm_token_in", "llm_token_out"):
            total_coin += rec.coin_cost or 0
            total_in += rec.llm_token_in or 0
            total_out += rec.llm_token_out or 0
        self.instance.coin_cost_total = total_coin
        self.instance.llm_token_in_total = total_in
        self.instance.llm_token_out_total = total_out
        self.instance.save(update_fields=[
            "coin_cost_total", "llm_token_in_total", "llm_token_out_total",
        ])

    # ─────────────────────────────────────────
    # 辅助：心跳（watchdog 用）
    # ─────────────────────────────────────────
    def _heartbeat(self) -> None:
        now = time.monotonic()
        if now - self._last_heartbeat < self._heartbeat_interval_seconds:
            return
        self._last_heartbeat = now
        self.instance.last_heartbeat_at = timezone.now()
        self.instance.save(update_fields=["last_heartbeat_at"])


# =========================================================
# 默认依赖实现 —— 通过 SkillBridge 接入技能运行层
# =========================================================
def _default_agent_runner(
    *,
    project: Any,
    node_config: NodeConfig,
    context: Dict[str, Any],
    dry_run: bool = False,
) -> Any:
    """工作流引擎调用节点技能的统一入口。

    通过 SkillBridge 路由到：
      A. SkillInvoker（skill_id 已注册到 FusionPipelineNode）
      B. Python 函数（runner_path 已注册）

    不再直接依赖旧创作节点模块；所有技能通过 SkillBridge 解耦。
    """
    from apps.workflow.skill_bridge import run_workflow_node as _run_workflow_node

    result = _run_workflow_node(
        project=project,
        node_config=node_config,
        context=context or {},
        dry_run=dry_run,
    )

    # 转换为 engine 内部 NodeRunResult 格式
    if result.success:
        class _OkResult:
            status = "completed"
            meta: Dict[str, Any] = {}
            outputs: Dict[str, Any] = dict(result.output)
            outputs.setdefault("coin_cost", result.coin_cost)
            outputs.setdefault("llm_token_in", result.llm_token_in)
            outputs.setdefault("llm_token_out", result.llm_token_out)
            errors: List[str] = []
        return _OkResult()
    else:
        class _FailResult:
            status = "failed"
            meta: Dict[str, Any] = {}
            outputs: Dict[str, Any] = {}
            errors: List[str] = list(result.errors)
        return _FailResult()


def _default_billing_ok(*args: Any, **kwargs: Any) -> bool:
    """暂不对接真实计费（P1 阶段接入）。"""
    return True


# =========================================================
# 监控友好函数：从数据库读取实例执行进度
# =========================================================
def get_instance_progress(instance: WorkflowInstance) -> Dict[str, Any]:
    """为前端进度条准备结构化数据。"""
    nodes = list(
        NodeExecution.objects.filter(instance=instance).order_by("created_at")
    )
    total_planned = max(
        1, instance.pack.nodes.filter(enabled=True).count() or len(nodes)
    )
    done = sum(1 for n in nodes if n.status in ("succeeded", "skipped"))
    failed = sum(1 for n in nodes if n.status == "failed")
    running_count = sum(1 for n in nodes if n.status == "running")
    pct = min(99, int(done * 100 / total_planned)) if total_planned else 0

    if instance.status == "done":
        pct = 100
    elif instance.status in ("failed", "cancelled"):
        pct = max(pct, 5)  # 显示为中断进度

    # 汇总计费
    coin = sum((n.coin_cost or 0) for n in nodes)
    token_in = sum((n.llm_token_in or 0) for n in nodes)
    token_out = sum((n.llm_token_out or 0) for n in nodes)

    timeline = []
    for n in nodes:
        timeline.append({
            "node_id": n.node_id,
            "node_name": n.node_name,
            "runner_type": n.runner_type,
            "status": n.status,
            "duration_ms": n.duration_ms or 0,
            "coin_cost": n.coin_cost or 0,
            "retry": n.attempt or 0,
            "created_at": _fmt_dt(n.created_at),
        })

    return {
        "instance_id": str(instance.id),
        "status": instance.status,
        "current_node_id": instance.current_node_id,
        "progress_pct": pct,
        "total_nodes": total_planned,
        "done_nodes": done,
        "running_nodes": running_count,
        "failed_nodes": failed,
        "coin_used": coin,
        "llm_token_in": token_in,
        "llm_token_out": token_out,
        "elapsed_seconds": int(
            (timezone.now() - (instance.started_at or instance.created_at))
            .total_seconds()
        ) if instance.started_at else 0,
        "timeline": timeline,
    }


def _fmt_dt(dt: Optional[datetime]) -> str:
    if dt is None:
        return ""
    return dt.isoformat()


__all__ = [
    "WorkflowEngine",
    "NodeConfig",
    "NodeRunResult",
    "get_instance_progress",
]
