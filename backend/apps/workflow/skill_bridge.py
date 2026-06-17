# -*- coding: utf-8 -*-
"""工作流引擎 → 技能运行层桥接
========================================================
WorkflowEngine 的节点执行通过 SkillBridge 接入实际技能运行层。

设计原则：
  ① 工作流引擎完全不感知"技能如何实现"，只调用 SkillBridge.run()
  ② SkillBridge 根据节点的 skill_id 或 runner_path 路由到具体实现
  ③ SkillBridge 兼容两种路径：
      A. skill_id → SkillInvoker（LLM 型技能，有 schema）
      B. runner_path → 任意 Python 函数（创作节点 / 质检 / 评分 等）

节点 skill_id 注册方式（FusionPipelineNode）：
  • skill_id 字段 → 直接作为 skill_id 传给 SkillInvoker.invoke()
  • runner_path 字段 → 直接 import + 调用（保留旧创作节点的迁移路径）

典型节点注册示例：
  FusionPipelineNode(
    fusion_node_id="node_brief",
    name="立项定义",
    runner_type="fusion_node",
    skill_id="creation.brief",
    # skill_id 存在 → 调用 SkillInvoker.invoke("creation.brief", ...)
    coin_cost=30,
  )

  FusionPipelineNode(
    fusion_node_id="node_review",
    name="质量审查",
    runner_type="fusion_review",
    runner_path="apps.creation.orchestration.review.run_review_node",
    # skill_id 不存在，按 runner_path 调用
    coin_cost=10,
  )
========================================================
"""
from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# =========================================================
# SkillBridgeResult — 节点执行结果的统一格式
# =========================================================
@dataclass
class SkillBridgeResult:
    """SkillBridge 对 workflow_engine 返回的统一结果。"""
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    errors: list = field(default_factory=list)
    coin_cost: int = 0
    llm_token_in: int = 0
    llm_token_out: int = 0
    duration_ms: int = 0
    run_ids: list = field(default_factory=list)   # 审计用（AgentExecutionRun IDs）
    retryable: bool = False                       # 告知引擎是否可重试


# =========================================================
# SkillBridge — 统一入口
# =========================================================
class SkillBridge:
    """工作流节点 → 技能运行层的唯一桥梁。"""

    def __init__(self, project: Any, node_config: Any, context: Dict[str, Any]):
        self.project = project
        self.node_config = node_config
        self.context = context
        self._invoker = None

    # ─────────────────────────────────────────
    # 统一入口（引擎唯一调用点）
    # ─────────────────────────────────────────
    def run(self, dry_run: bool = False) -> SkillBridgeResult:
        """执行节点技能，返回统一结果。

        路由逻辑：
          1. 有 skill_id → SkillInvoker.invoke()
          2. 无 skill_id 但有 runner_path → 按路径调用 Python 函数
          3. 两者都没有 → 返回失败
        """
        skill_id = getattr(self.node_config, "skill_id", None) or ""
        runner_path = getattr(self.node_config, "runner_path", None) or ""
        node_id = getattr(self.node_config, "node_id", "?")
        extra_config = getattr(self.node_config, "extra_config", None) or {}
        coin_cost = getattr(self.node_config, "coin_cost", 0) or 0

        if dry_run:
            return SkillBridgeResult(
                success=True,
                output={"content": f"(dry-run output for {node_id})"},
                coin_cost=coin_cost,
                duration_ms=0,
            )

        # 路由 A: skill_id → LLM 型技能（通过 SkillInvoker）
        if skill_id:
            return self._run_via_skill_invoker(
                skill_id=skill_id,
                node_id=node_id,
                extra_config=extra_config,
                coin_cost=coin_cost,
            )

        # 路由 B: runner_path → 直接 Python 函数
        if runner_path:
            return self._run_via_runner_path(
                runner_path=runner_path,
                node_id=node_id,
                extra_config=extra_config,
                coin_cost=coin_cost,
            )

        # 兜底：两者都没有
        logger.error("[SkillBridge] 节点 %s 既无 skill_id 也无 runner_path", node_id)
        return SkillBridgeResult(
            success=False,
            errors=[f"节点 {node_id} 未注册 skill_id 或 runner_path"],
            retryable=False,
        )

    # ─────────────────────────────────────────
    # 路由 A: SkillInvoker（LLM 型技能）
    # ─────────────────────────────────────────
    def _run_via_skill_invoker(
        self,
        skill_id: str,
        node_id: str,
        extra_config: Dict[str, Any],
        coin_cost: int,
    ) -> SkillBridgeResult:
        """通过 SkillInvoker 调用 LLM 型技能。"""
        import time
        t0 = time.time()

        try:
            from apps.skill.skills.invoker import get_skill_invoker

            invoker = get_skill_invoker()

            # 构建 payload：从 context 中提取相关上下文 + extra_config
            payload = self._build_skill_payload(skill_id, extra_config)

            result = invoker.invoke(
                skill_id=skill_id,
                payload=payload,
                project_id=str(self.project.id) if self.project else None,
                user_id=self._extract_user_id(),
            )

            duration_ms = int((time.time() - t0) * 1000)
            llm_in = result.meta.get("llm_token_in", 0)
            llm_out = result.meta.get("llm_token_out", 0)
            actual_cost = int(result.meta.get("quota_cost", coin_cost) or coin_cost)

            return SkillBridgeResult(
                success=result.success,
                output=result.data or {},
                errors=[result.error.get("message", "")] if result.error else [],
                coin_cost=actual_cost,
                llm_token_in=llm_in,
                llm_token_out=llm_out,
                duration_ms=duration_ms,
                run_ids=[result.meta.get("trace_id", "")],
                retryable=(
                    result.error.get("code") not in (
                        _get_code("SKILL_NOT_FOUND"),
                        _get_code("SKILL_DISABLED"),
                        _get_code("SKILL_LIFECYCLE_ERROR"),
                        _get_code("SKILL_VALIDATION_ERROR"),
                        _get_code("SKILL_QUOTA_EXCEEDED"),
                    )
                    if result.error else True
                ),
            )

        except Exception as exc:
            duration_ms = int((time.time() - t0) * 1000)
            logger.exception("[SkillBridge] SkillInvoker 调用失败 skill=%s", skill_id)
            return SkillBridgeResult(
                success=False,
                errors=[f"{type(exc).__name__}:{exc}"],
                coin_cost=coin_cost,
                duration_ms=duration_ms,
                retryable=True,
            )

    def _build_skill_payload(
        self,
        skill_id: str,
        extra_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """从 instance.context 提取技能所需上下文，构建 payload。"""
        ctx = self.context or {}

        # 基础 payload：从 extra_config 合并
        payload = dict(extra_config)

        # 注入全局上下文（key 映射：简化版）
        for key in ("theme", "topic", "format", "duration"):
            if key in ctx:
                payload[key] = ctx[key]

        # 注入前一节点输出
        prev_output = ctx.get("prev", {})
        if prev_output:
            payload["prev_output"] = prev_output

        # 注入已完成的节点输出
        nodes_output = ctx.get("nodes", {})
        if nodes_output:
            payload["completed_nodes"] = nodes_output

        return payload

    def _extract_user_id(self) -> Optional[int]:
        """从 project 中提取 user_id。"""
        try:
            return int(getattr(self.project, "user_id", None)
                      or getattr(self.project, "user", None))
        except Exception:
            return None

    # ─────────────────────────────────────────
    # 路由 B: Python 函数（创作节点 / 质检 / 评分等）
    # ─────────────────────────────────────────
    def _run_via_runner_path(
        self,
        runner_path: str,
        node_id: str,
        extra_config: Dict[str, Any],
        coin_cost: int,
    ) -> SkillBridgeResult:
        """按 runner_path 动态导入并调用 Python 函数。

        对于旧创作节点（workspace_bridge 体系），runner_path 为：
          "apps.creation.orchestration.workspace_bridge.run_workspace_node"
        需要适配 WorkspaceInvokeOptions(node_index=chain_order, ...) 签名。
        """
        import time
        t0 = time.time()

        try:
            # ── 特殊路由：workspace_bridge（旧创作节点体系）────────
            if runner_path.endswith("workspace_bridge.run_workspace_node"):
                return self._run_workspace_bridge_node(
                    node_id=node_id,
                    extra_config=extra_config,
                    coin_cost=coin_cost,
                    t0=t0,
                )

            # ── 通用路由：直接 import + 调用 Python 函数 ─────────
            module_name, func_name = runner_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            func = getattr(module, func_name, None)
            if func is None:
                raise AttributeError(f"模块 {module_name} 中没有 {func_name}")

            # 兼容多种旧签名
            import inspect
            sig = inspect.signature(func)
            if len(sig.parameters) >= 3:
                raw_result = func(self.project, self.node_config, self.context)
            else:
                raw_result = func(self.project, self.node_config, self.context, extra_config)

            return self._normalize_result(raw_result, coin_cost, t0)

        except Exception as exc:
            duration_ms = int((time.time() - t0) * 1000)
            logger.exception("[SkillBridge] runner_path 调用失败 path=%s", runner_path)
            return SkillBridgeResult(
                success=False,
                errors=[f"{type(exc).__name__}:{exc}"],
                coin_cost=coin_cost,
                duration_ms=duration_ms,
                retryable=True,
            )

    def _run_workspace_bridge_node(
        self,
        node_id: str,
        extra_config: Dict[str, Any],
        coin_cost: int,
        t0: float,
    ) -> SkillBridgeResult:
        """适配旧创作节点（workspace_bridge）：

        将 NodeConfig.chain_order（节点顺序）映射为 WorkspaceInvokeOptions.node_index，
        通过旧 AgentOrchestrator 体系执行节点，返回统一 SkillBridgeResult。

        这是迁移期的桥接层：SkillBridge 对外只暴露统一协议，
        内部适配旧节点的 WorkspaceInvokeOptions 签名。
        """
        import time

        try:
            from apps.creation.orchestration.types import AgentResult, WorkspaceInvokeOptions

            node_index = self.node_config.chain_order
            if node_index <= 0:
                node_index = 1

            opts = WorkspaceInvokeOptions(
                node_index=node_index,
                script_from=extra_config.get("script_from"),
                script_to=extra_config.get("script_to"),
                outline_mode=extra_config.get("outline_mode"),
                outline_from=extra_config.get("outline_from"),
                outline_to=extra_config.get("outline_to"),
                outline_stage_key=extra_config.get("outline_stage_key"),
            )

            from apps.creation.orchestration.workspace_bridge import run_workspace_node
            agent_result: AgentResult = run_workspace_node(self.project, opts)

            duration_ms = int((time.time() - t0) * 1000)
            success = agent_result.status in ("completed", "success", "done")
            outputs = agent_result.outputs or {}
            return SkillBridgeResult(
                success=success,
                output=dict(outputs),
                errors=list(agent_result.errors or []),
                coin_cost=int(outputs.get("coin_cost", coin_cost) or coin_cost),
                llm_token_in=int(outputs.get("llm_token_in", 0) or 0),
                llm_token_out=int(outputs.get("llm_token_out", 0) or 0),
                duration_ms=duration_ms,
                run_ids=[str(getattr(agent_result, "run_id", ""))],
                retryable=not success,
            )

        except Exception as exc:
            duration_ms = int((time.time() - t0) * 1000)
            logger.exception("[SkillBridge] workspace_bridge 调用失败 node_id=%s", node_id)
            return SkillBridgeResult(
                success=False,
                errors=[f"{type(exc).__name__}:{exc}"],
                coin_cost=coin_cost,
                duration_ms=duration_ms,
                retryable=True,
            )

    def _normalize_result(
        self,
        raw: Any,
        coin_cost: int,
        t0: float,
    ) -> SkillBridgeResult:
        """将各种旧格式结果标准化为 SkillBridgeResult。"""
        import time
        duration_ms = int((time.time() - t0) * 1000)

        # 情况 1: 已经是 SkillBridgeResult
        if isinstance(raw, SkillBridgeResult):
            return raw

        # 情况 2: 字典（节点输出）
        if isinstance(raw, dict):
            return SkillBridgeResult(
                success=bool(raw.get("ok") or raw.get("success")),
                output=raw,
                coin_cost=int(raw.get("coin_cost", coin_cost) or coin_cost),
                llm_token_in=int(raw.get("llm_token_in", 0) or 0),
                llm_token_out=int(raw.get("llm_token_out", 0) or 0),
                duration_ms=int(raw.get("duration_ms", duration_ms) or duration_ms),
            )

        # 情况 3: 有 status 属性的对象（兼容旧 AgentResult）
        if hasattr(raw, "status"):
            status = getattr(raw, "status", "")
            success = status in ("completed", "success", "done")
            outputs = getattr(raw, "outputs", {}) or {}
            return SkillBridgeResult(
                success=success,
                output=dict(outputs) if isinstance(outputs, dict) else {},
                errors=list(getattr(raw, "errors", None) or []),
                coin_cost=int(outputs.get("coin_cost", coin_cost) or coin_cost),
                llm_token_in=int(outputs.get("llm_token_in", 0) or 0),
                llm_token_out=int(outputs.get("llm_token_out", 0) or 0),
                duration_ms=duration_ms,
            )

        # 兜底
        return SkillBridgeResult(
            success=True,
            output={"content": str(raw)},
            coin_cost=coin_cost,
            duration_ms=duration_ms,
        )


# =========================================================
# 工具函数
# =========================================================
_code_cache: Dict[str, int] = {}


def _get_code(name: str) -> int:
    if name not in _code_cache:
        try:
            from apps.common.exceptions import _CODES
            _code_cache[name] = _CODES.get(name, 0)
        except Exception:
            _code_cache[name] = 0
    return _code_cache[name]


# =========================================================
# 便捷入口（供 workflow_engine._default_agent_runner 调用）
# =========================================================
def run_workflow_node(
    project: Any,
    node_config: Any,
    context: Dict[str, Any],
    dry_run: bool = False,
) -> SkillBridgeResult:
    """工作流引擎调用节点技能的唯一入口。

    等价于:
        bridge = SkillBridge(project, node_config, context)
        return bridge.run(dry_run=dry_run)
    """
    return SkillBridge(project, node_config, context).run(dry_run=dry_run)


__all__ = [
    "SkillBridge",
    "SkillBridgeResult",
    "run_workflow_node",
]
