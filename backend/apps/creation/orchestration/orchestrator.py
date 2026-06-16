# -*- coding: utf-8 -*-
"""AgentOrchestrator：统一调度入口。"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from ..artifact_service import get_artifact
from ..monitoring.execution_run_service import AgentExecutionRunService
from ..models import Project
from apps.agent.runtime import (
    agent_for_pipeline_node_index,
    agent_for_workspace_index,
    polish_max_rounds,
    post_script_effective_chain,
    primary_output_artifact,
    resolve_agent_runner,
    should_defer_to_post_script_chain,
)
from .types import AgentResult, WorkspaceInvokeOptions
from .workspace_bridge import run_workspace_node

logger = logging.getLogger(__name__)


def _runner_type_for_pipeline_index(node_index: int) -> str:
    from apps.workflow.fusion import FusionNodeRegistry

    runner_type = FusionNodeRegistry().runner_type_for_index(int(node_index))
    if runner_type:
        return runner_type
    idx = int(node_index)
    if idx <= 5:
        return "fusion_node"
    if idx == 6:
        return "fusion_review"
    if idx == 7:
        return "fusion_score"
    return ""


def _artifact_key_for_step(node_index: int, result: AgentResult) -> str:
    from apps.workflow.fusion import FusionNodeRegistry, get_artifact_registry

    artifact_key = (result.outputs or {}).get("artifact_key")
    if artifact_key:
        return str(artifact_key)
    node_id = FusionNodeRegistry().fusion_node_id_for_index(int(node_index))
    if node_id:
        key = get_artifact_registry().primary_artifact_for_fusion_node(node_id)
        if key:
            return key
    agent_id = agent_for_pipeline_node_index(int(node_index)) or result.agent_id
    return primary_output_artifact(agent_id)


def agent_result_to_workspace_step(result: AgentResult, node_index: int) -> Dict[str, Any]:
    if result.status == "error":
        return {"status": "error", "errors": list(result.errors or ["Agent 执行失败"])}
    return {
        "status": "completed",
        "node_index": int(node_index),
        "agent_id": result.agent_id,
        "artifact_key": _artifact_key_for_step(node_index, result),
    }


def agent_result_to_fusion_post_step(result: AgentResult, node_index: int) -> Dict[str, Any]:
    """质检/评分步骤：保留 ok/skipped 供 step_mode 校验。"""
    if result.status == "error":
        return {"status": "error", "errors": list(result.errors or ["执行失败"])}
    fusion = dict((result.meta or {}).get("fusion") or {})
    return {
        "status": "completed",
        "node_index": int(node_index),
        "agent_id": result.agent_id,
        "ok": bool(fusion.get("ok", True)),
        "skipped": bool(fusion.get("skipped")),
        "error": fusion.get("error") or "",
    }


class AgentOrchestrator:
    def __init__(self, project: Project):
        self.project = project

    def invoke_adapt_on_create(self, submit_data: Optional[Dict[str, Any]] = None) -> AgentResult:
        runner = resolve_agent_runner("adapt")
        if not runner:
            return AgentResult(agent_id="adapt", status="error", errors=["AdaptAgent runner 未配置"])
        return AgentExecutionRunService.run_tracked_agent(
            self.project,
            "adapt",
            runner,
            node_index=0,
            input_summary={
                "creation_entry": self.project.creation_entry or "",
                "submit_keys": sorted((submit_data or {}).keys()),
            },
            submit_data=submit_data,
        )

    # 节点 → 所需上游产物（按最小依赖原则，node-1 无依赖）
    _UPSTREAM_DEPS: Dict[int, tuple] = {
        2: ("project_brief",),
        3: ("project_brief", "structure_plan"),
        4: ("project_brief", "structure_plan", "character_bible"),
        5: ("project_brief", "structure_plan", "character_bible", "series_outline"),
    }

    def _check_artifact_deps(self, node_index: int) -> Optional[str]:
        """
        前置 artifact 就绪检查，在进入具体 Agent 之前快速失败。
        复用 artifact_readiness.require_upstream_artifacts，避免在 Agent 内部才发现依赖缺失。
        返回 None 表示全部就绪，返回字符串表示缺失提示。
        """
        from ..artifact_readiness import require_upstream_artifacts

        keys = self._UPSTREAM_DEPS.get(int(node_index))
        if not keys:
            return None
        return require_upstream_artifacts(self.project, keys)

    def invoke_workspace(self, options: WorkspaceInvokeOptions) -> AgentResult:
        agent_id = agent_for_workspace_index(options.node_index)
        logger.info(
            "[Orchestrator] workspace agent=%s node=%s project=%s",
            agent_id,
            options.node_index,
            self.project.id,
        )
        if should_defer_to_post_script_chain(self.project, options.node_index):
            deferred_id = agent_for_pipeline_node_index(options.node_index) or agent_id or "post_script"
            return AgentResult(
                agent_id=deferred_id,
                status="skipped",
                meta={
                    "fusion": {
                        "skipped": True,
                        "reason": "workspace_post_script_chain",
                        "message": "工作台模式下由 post_script_chain 统一执行",
                    }
                },
            )
        if int(options.node_index) >= 2:
            from ..workspace.workspace_content import ensure_brief_seed_enriched

            ensure_brief_seed_enriched(self.project)
        # 前置依赖检查：上游 artifact 未就绪则立即返回，不消耗任何 LLM token
        dep_error = self._check_artifact_deps(options.node_index)
        if dep_error:
            logger.warning(
                "[Orchestrator] 依赖未就绪，跳过执行 node=%s project=%s reason=%s",
                options.node_index,
                self.project.id,
                dep_error,
            )
            return AgentResult(
                agent_id=agent_id or f"node-{options.node_index}",
                status="error",
                errors=[dep_error],
            )
        return run_workspace_node(self.project, options)

    def invoke_pipeline_step(
        self,
        node_index: int,
        *,
        script_from: Optional[int] = None,
        script_to: Optional[int] = None,
        outline_mode: Optional[str] = None,
        outline_from: Optional[int] = None,
        outline_to: Optional[int] = None,
    ) -> Dict[str, Any]:
        """流水线单步：按 runner_type 调度 registry 中的 Agent，不直接控制子技能。"""
        idx = int(node_index)
        runner_type = _runner_type_for_pipeline_index(idx)
        agent_id = agent_for_pipeline_node_index(idx)

        logger.info(
            "[Orchestrator] pipeline step node=%s runner_type=%s agent=%s project=%s",
            idx,
            runner_type,
            agent_id,
            self.project.id,
        )

        if runner_type == "fusion_review":
            result = self.invoke(agent_id or "review")
            return agent_result_to_fusion_post_step(result, idx)

        if runner_type == "fusion_score":
            result = self.invoke(agent_id or "score")
            return agent_result_to_fusion_post_step(result, idx)

        if runner_type == "fusion_node":
            if not agent_id:
                return {"status": "error", "errors": [f"节点 {idx} 未在 Agent Registry 配置"]}
            opts = WorkspaceInvokeOptions(
                node_index=idx,
                script_from=script_from,
                script_to=script_to,
                outline_mode=outline_mode,
                outline_from=outline_from,
                outline_to=outline_to,
            )
            if outline_mode == "episodes":
                opts.outline_from = outline_from if outline_from is not None else script_from
                opts.outline_to = outline_to if outline_to is not None else script_to
            result = self.invoke_workspace(opts)
            return agent_result_to_workspace_step(result, idx)

        return {
            "status": "error",
            "errors": [f"节点 {idx} runner_type={runner_type!r} 不支持由调度引擎执行"],
        }

    def scripts_fully_generated(self) -> bool:
        scripts = get_artifact(self.project, "episode_scripts") or {}
        eps = scripts.get("episodes") or []
        if not eps:
            return False
        nums = {
            int(e.get("episodeNumber") or e.get("episode") or 0)
            for e in eps
            if isinstance(e, dict)
        }
        nums.discard(0)
        target = int(self.project.episode_count or 0)
        if target <= 0:
            return len(nums) > 0
        return len(nums) >= target

    def run_post_script_chain(self) -> Dict[str, Any]:
        """按 registry 配置执行剧本后处理链，接入 ConvergenceService 四态停机控制。"""
        from ..convergence_service import ConvergenceService
        from ..models import CreationNode
        from django.db import transaction

        chain = post_script_effective_chain()
        results: List[Dict[str, Any]] = []
        review_report: Optional[Dict[str, Any]] = None
        polish_rounds = 0
        convergence_svc = ConvergenceService.from_thresholds()

        def _get_or_create_review_node() -> Optional[CreationNode]:
            """获取或创建 review 节点（node_index=6），用于收敛状态跟踪。"""
            try:
                node, _ = CreationNode.objects.get_or_create(
                    project=self.project,
                    node_index=6,
                    defaults={
                        "node_name": "质检与审核",
                        "node_role": CreationNode.ROLE_REVIEW,
                        "fusion_node_id": "node-6-review",
                        "max_fix_rounds": 5,
                    },
                )
                return node
            except Exception as exc:  # noqa: BLE001
                logger.warning("[Orchestrator] 获取 review 节点失败: %s", exc)
                return None

        def _extract_score_from_report() -> Optional[float]:
            """从 score_report artifact 提取数值总分。"""
            sr = get_artifact(self.project, "script_score_report") or {}
            score = sr.get("finalScore") or sr.get("fiveDimensionScore")
            if score is not None:
                return float(score)
            rr = get_artifact(self.project, "score_report") or {}
            score = rr.get("overallScore")
            if score is not None:
                return float(score)
            return None

        review_node = _get_or_create_review_node()

        for step in chain:
            runner = resolve_agent_runner(step)
            if not runner:
                results.append(
                    AgentResult(
                        agent_id=step,
                        status="error",
                        errors=[f"Agent runner 未配置: {step}"],
                    ).to_dict()
                )
                continue
            if step == "review":
                # 收敛检查：如果已停机，跳过 review-polish 回路
                if review_node:
                    can, reason = convergence_svc.can_fix(review_node)
                    if not can:
                        skipped = AgentResult(
                            agent_id="review",
                            status="skipped",
                            meta={"reason": "convergence_blocked", "message": reason},
                        )
                        results.append(skipped.to_dict())
                        logger.info(
                            "[Orchestrator] review 已停机，跳过 project=%s reason=%s",
                            self.project.id, reason,
                        )
                        continue

                result = AgentExecutionRunService.run_tracked_agent(
                    self.project,
                    "review",
                    runner,
                    input_summary={"chain": "post_script", "step": "review"},
                )
                results.append(result.to_dict())
                review_report = (result.outputs or {}).get("review_report") or get_artifact(
                    self.project, "review_report"
                )
            elif step == "polish":
                if polish_rounds >= polish_max_rounds():
                    skipped = AgentResult(
                        agent_id="polish",
                        status="skipped",
                        meta={"reason": "max_rounds"},
                    )
                    results.append(skipped.to_dict())
                    continue
                result = AgentExecutionRunService.run_tracked_agent(
                    self.project,
                    "polish",
                    runner,
                    input_summary={
                        "chain": "post_script",
                        "step": "polish",
                        "review_passed": bool((review_report or {}).get("passed")),
                    },
                    review_report=review_report,
                )
                polish_rounds += 1
                results.append(result.to_dict())
            elif step == "score":
                result = AgentExecutionRunService.run_tracked_agent(
                    self.project,
                    "score",
                    runner,
                    input_summary={"chain": "post_script", "step": "score"},
                )
                results.append(result.to_dict())

                # score 完成后向 ConvergenceService 记录分数，触发四态判定
                if review_node and result.status == "completed":
                    score_val = _extract_score_from_report()
                    if score_val is not None:
                        try:
                            conv_result = convergence_svc.record_score(review_node, score_val)
                            review_node.refresh_from_db()
                            logger.info(
                                "[Orchestrator] 收敛判定 project=%s score=%.2f state=%s can_fix=%s",
                                self.project.id, score_val,
                                conv_result.state, conv_result.can_fix,
                            )
                        except Exception as exc:  # noqa: BLE001
                            logger.warning("[Orchestrator] ConvergenceService 记录失败: %s", exc)
            else:
                result = AgentExecutionRunService.run_tracked_agent(
                    self.project,
                    step,
                    runner,
                    input_summary={"chain": "post_script", "step": step},
                )
                results.append(result.to_dict())

        ok = all(r.get("status") in ("completed", "skipped") for r in results)
        return {"status": "completed" if ok else "partial", "chain": chain, "results": results}

    def invoke(self, agent_id: str, **kwargs: Any) -> AgentResult:
        runner = resolve_agent_runner(agent_id)
        if not runner:
            return AgentResult(agent_id=agent_id, status="error", errors=[f"未知 Agent: {agent_id}"])
        return AgentExecutionRunService.run_tracked_agent(
            self.project,
            agent_id,
            runner,
            input_summary={"invoke": agent_id, "kwargs": sorted(kwargs.keys())},
            **kwargs,
        )


def run_workspace_node_by_index(
    project: Project,
    node_index: int,
    *,
    script_from: Optional[int] = None,
    script_to: Optional[int] = None,
    outline_mode: Optional[str] = None,
    outline_stage_key: Optional[str] = None,
) -> AgentResult:
    """tasks.py 工作台入口。"""
    opts = WorkspaceInvokeOptions(
        node_index=int(node_index),
        script_from=script_from,
        script_to=script_to,
        outline_mode=outline_mode,
        outline_stage_key=outline_stage_key,
    )
    if outline_mode == "episodes":
        opts.outline_from = script_from
        opts.outline_to = script_to
    orch = AgentOrchestrator(project)
    return orch.invoke_workspace(opts)


def run_pipeline_step_by_index(
    project: Project,
    node_index: int,
    *,
    script_from: Optional[int] = None,
    script_to: Optional[int] = None,
    outline_mode: Optional[str] = None,
    outline_from: Optional[int] = None,
    outline_to: Optional[int] = None,
) -> Dict[str, Any]:
    """分步流水线入口 — step_mode / fusion_orchestrator 统一走此函数。"""
    return AgentOrchestrator(project).invoke_pipeline_step(
        int(node_index),
        script_from=script_from,
        script_to=script_to,
        outline_mode=outline_mode,
        outline_from=outline_from,
        outline_to=outline_to,
    )


# =============================================================================
# PipelineOrchestrator — 基于 FusionPipelinePack 的通用编排器
# =============================================================================


class PipelineOrchestrator:
    """
    基于 FusionPipelinePack 的通用编排器。
    核心职责：
    - 根据用户 ID + gray_traffic_salt 稳定哈希决定命中哪个 pack 版本
    - 按 chain_order 顺序执行 enabled 的节点
    - 支持 SERIAL / CONDITION / HUMAN 节点类型
    - 统一进度上报（回调 SSE）
    """

    def __init__(self, project: Project):
        self.project = project

    # -------------------------------------------------------------------------
    # 灰度路由
    # -------------------------------------------------------------------------

    def resolve_pack(self) -> Optional["FusionPipelinePack"]:
        """
        灰度路由：按 gray_traffic_salt + user_id % 100 < gray_weight 决定命中哪个 pack。
        优先返回 pack_status=active 的；无 active 时返回 pack_status=gray 且命中灰度的。
        """
        # import 放函数内避免循环依赖
        from apps.workflow.models import FusionPipelinePack

        # 优先使用用户指定的 pack
        if self.project.pipeline_pack_id:
            pack = FusionPipelinePack.objects.filter(
                id=self.project.pipeline_pack_id,
            ).first()
            if pack and pack.pack_status in (FusionPipelinePack.PACK_ACTIVE, FusionPipelinePack.PACK_GRAY):
                return pack

        # 查找 active pack
        active_pack = FusionPipelinePack.objects.filter(
            pack_status=FusionPipelinePack.PACK_ACTIVE,
        ).order_by("-published_at").first()
        if active_pack:
            return active_pack

        # 灰度分流：从 gray pack 中按 user_id % 100 < gray_weight 决定命中
        gray_packs = FusionPipelinePack.objects.filter(
            pack_status=FusionPipelinePack.PACK_GRAY,
        ).order_by("-published_at")

        # 获取 gray_traffic_salt（Project 或 User 上的盐值，默认 0）
        salt = getattr(self.project, "gray_traffic_salt", None)
        if salt is None:
            salt = getattr(self.project.user, "gray_traffic_salt", 0) if self.project.user_id else 0

        user_id = self.project.user_id or 0
        bucket = (int(user_id) + int(salt or 0)) % 100

        for pack in gray_packs:
            if bucket < (pack.gray_weight or 100):
                return pack

        # 无命中灰度 pack，返回最新的 gray pack（用于展示）
        return gray_packs.first()

    # -------------------------------------------------------------------------
    # 主流程
    # -------------------------------------------------------------------------

    def run(self, pack: "FusionPipelinePack") -> Dict[str, Any]:
        """
        完整工作流执行主入口。
        按 pack.nodes.filter(enabled=True).order_by('chain_order') 依次执行。
        支持 SERIAL / PARALLEL / ITERATE / HUMAN 节点类型。
        返回 {"status": "completed"|"failed"|"partial"|"awaiting_user", "results": [...]}
        """
        from apps.workflow.models import FusionPipelineNode

        nodes = pack.nodes.filter(enabled=True).order_by("chain_order")
        results: List[Dict[str, Any]] = []
        all_ok = True

        total = nodes.count()
        last_stable_chain_order = 0  # 上一个稳定节点的 chain_order（用于失败回滚）
        for idx, node in enumerate(nodes):
            # 进度上报
            self.broadcast_progress(node, "running", {})

            # P1 阶段：按 node.runner_type 分发到对应执行器
            node_result = self._run_node(node, results)
            node_result["node_index"] = node.website_index
            node_result["fusion_node_id"] = node.fusion_node_id
            node_result["node_name"] = node.name
            results.append(node_result)

            # 更新项目进度
            self._update_project_progress(idx + 1, total)

            # 失败处理：PARALLEL/ITERATE 节点支持部分成功继续
            status = node_result.get("status")
            if status == "error":
                all_ok = False
                # 失败回滚到上一个稳定节点
                self._rollback_to_stable_node(last_stable_chain_order)
                break
            elif status == "awaiting_user":
                # HUMAN 节点暂停：直接返回，等待用户确认
                logger.info(
                    "[PipelineOrchestrator] HUMAN 节点暂停 node=%s project=%s",
                    node.fusion_node_id, self.project.id,
                )
                return {"status": "awaiting_user", "results": results}
            elif status in ("completed", "auto_skipped", "partial"):
                # PARALLEL/ITERATE 部分成功也记为稳定节点，不中断
                last_stable_chain_order = node.chain_order
            else:
                last_stable_chain_order = node.chain_order

        return {
            "status": "completed" if all_ok else "partial",
            "results": results,
        }

    # -------------------------------------------------------------------------
    # P1 阶段：节点分发器（按 runner_type 分支）
    # -------------------------------------------------------------------------

    def _run_node(self, node: "FusionPipelinePack", results: list) -> Dict[str, Any]:
        """
        单节点执行器（按 runner_type 分支）。

        支持的 runner_type：
        - "fusion_node" / "fusion_review" / "fusion_score" / "agent_chain"  → SERIAL
        - "parallel_group"  → PARALLEL：同级多节点并发执行
        - "iterate_loop"    → ITERATE：循环迭代直到达成条件
        - "human_gate"      → HUMAN：step 模式暂停等待用户确认
        """
        from apps.workflow.models import FusionPipelineNode

        rt = node.runner_type or FusionPipelineNode.RUNNER_FUSION_NODE
        start = time.monotonic()

        try:
            if rt == FusionPipelineNode.RUNNER_PARALLEL_GROUP:
                result = self._run_parallel_node(node, results)
            elif rt == FusionPipelineNode.RUNNER_ITERATE_LOOP:
                result = self._run_iterate_node(node, results)
            elif rt == FusionPipelineNode.RUNNER_HUMAN_GATE:
                result = self._run_human_gate_node(node, results)
            elif rt == "external_api":
                result = self._run_external_api_node(node, results)
            else:
                # SERIAL 分支：保持原 run_node 行为完全不变（向后兼容）
                result = self._run_serial_node(node)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "[PipelineOrchestrator] _run_node 异常 node=%s runner_type=%s: %s",
                node.fusion_node_id, rt, exc,
            )
            result = {
                "status": "error",
                "errors": [f"节点执行异常: {exc}"],
            }

        # 记录执行耗时到 meta.duration_ms（便于监控与对账）
        duration_ms = int((time.monotonic() - start) * 1000)
        meta = dict(result.get("meta") or {})
        meta["duration_ms"] = duration_ms
        meta["runner_type"] = rt
        result["meta"] = meta
        return result

    def _run_serial_node(self, node: "FusionPipelinePack") -> Dict[str, Any]:
        """
        SERIAL 节点执行器：复用原 run_node 逻辑。
        支持 fusion_node / fusion_review / fusion_score / agent_chain。
        """
        idx = int(node.website_index)
        runner_type = _runner_type_for_pipeline_index(idx)
        agent_id = agent_for_pipeline_node_index(idx)

        logger.info(
            "[PipelineOrchestrator] _run_serial_node node=%s runner_type=%s agent=%s project=%s",
            node.fusion_node_id,
            runner_type,
            agent_id,
            self.project.id,
        )

        # 根据 runner_type 分发
        if runner_type == "fusion_review":
            result = self._invoke_agent(agent_id or "review", node)
            return agent_result_to_fusion_post_step(result, idx)

        if runner_type == "fusion_score":
            result = self._invoke_agent(agent_id or "score", node)
            return agent_result_to_fusion_post_step(result, idx)

        if runner_type == "fusion_node":
            # 复用 AgentOrchestrator 的 invoke_pipeline_step 逻辑
            step_result = AgentOrchestrator(self.project).invoke_pipeline_step(idx)
            # 写入 artifact
            artifact_key = node.artifact_key or step_result.get("artifact_key", "")
            if artifact_key:
                from ..artifact_service import save_artifact

                artifact_payload = step_result.get("outputs", {})
                save_artifact(self.project, artifact_key, artifact_payload)
            return step_result

        return {
            "status": "error",
            "errors": [f"节点类型 {runner_type!r} 暂不支持由 PipelineOrchestrator 执行"],
        }

    def _run_parallel_node(self, parent_node: "FusionPipelinePack", results: list) -> Dict[str, Any]:
        """
        PARALLEL 节点：执行同 group_key 的所有 SERIAL 节点。

        并发执行：使用 concurrent.futures.ThreadPoolExecutor 最多 4 并发。
        合并结果：将所有子节点输出聚合到 parent_node 的 artifact_key。
        失败处理：单节点异常被 try/except 捕获，不中断整体流程，最终 status=partial。
        """
        from apps.workflow.models import FusionPipelineNode

        group_key = (parent_node.extra_config or {}).get(
            "parallel_group_key", parent_node.fusion_node_id,
        )
        # 找到同 pack 下 extra_config.parallel_group_key == group_key 的所有 enabled 节点
        siblings_qs = FusionPipelineNode.objects.filter(
            pack_id=parent_node.pack_id,
            enabled=True,
            extra_config__parallel_group_key=group_key,
        ).exclude(id=parent_node.id).order_by("chain_order")

        siblings = list(siblings_qs)
        if not siblings:
            logger.warning(
                "[PipelineOrchestrator] PARALLEL 节点未找到同 group_key=%s 的兄弟节点 parent=%s",
                group_key, parent_node.fusion_node_id,
            )
            return {
                "status": "completed",
                "parallel_results": [],
                "group_key": group_key,
                "message": "未配置同组兄弟节点，PARALLEL 节点直接通过",
            }

        # 并发执行：单节点异常不中断整体流程
        parallel_results: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._run_serial_node, sib): sib
                for sib in siblings
            }
            for future in as_completed(futures):
                sib = futures[future]
                try:
                    sub_result = future.result()
                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "[PipelineOrchestrator] parallel 子节点失败 fusion_node_id=%s: %s",
                        sib.fusion_node_id, exc,
                    )
                    sub_result = {
                        "status": "failed",
                        "errors": [str(exc)],
                        "fusion_node_id": sib.fusion_node_id,
                    }
                sub_result.setdefault("fusion_node_id", sib.fusion_node_id)
                sub_result.setdefault("node_name", sib.name)
                parallel_results.append(sub_result)

        all_ok = all(r.get("status") in ("completed", "auto_skipped") for r in parallel_results)
        merged_status = "completed" if all_ok else "partial"
        result: Dict[str, Any] = {
            "status": merged_status,
            "parallel_results": parallel_results,
            "group_key": group_key,
            "sibling_count": len(parallel_results),
        }
        # 合并子节点产物到 parent_node.artifact_key
        artifact_key = parent_node.artifact_key or f"parallel_{group_key}"
        if artifact_key:
            from ..artifact_service import save_artifact
            try:
                merged_payload = {
                    "group_key": group_key,
                    "siblings": parallel_results,
                }
                save_artifact(self.project, artifact_key, merged_payload)
                result["artifact_key"] = artifact_key
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[PipelineOrchestrator] PARALLEL 合并 artifact 失败 artifact_key=%s: %s",
                    artifact_key, exc,
                )
        return result

    def _run_iterate_node(self, node: "FusionPipelinePack", results: list) -> Dict[str, Any]:
        """
        ITERATE 节点：循环执行某节点 N 次或直到评分达标。

        条件来源（优先级）：
        1. node.extra_config.iterate_max_attempts  (默认 3)
        2. node.extra_config.iterate_until_condition
           (e.g. {"field": "overall_score", "operator": ">=", "value": 70})
        3. 评分提升：上次 vs 这次评分差 < 1 分 也算达标（防止无意义循环）
        """
        from apps.workflow.models import FusionPipelineNode

        extra = node.extra_config or {}
        try:
            max_attempts = int(extra.get("iterate_max_attempts", 3))
        except (TypeError, ValueError):
            max_attempts = 3
        until_condition = extra.get("iterate_until_condition")
        target_node_id = extra.get("iterate_target_node_id")

        if not target_node_id:
            logger.warning(
                "[PipelineOrchestrator] ITERATE 节点未配置 iterate_target_node_id node=%s",
                node.fusion_node_id,
            )
            return {
                "status": "error",
                "errors": ["ITERATE 节点缺少 iterate_target_node_id 配置"],
            }

        # 找到目标 SERIAL 节点（必须在同 pack 下）
        try:
            target_node = FusionPipelineNode.objects.get(
                pack_id=node.pack_id,
                fusion_node_id=target_node_id,
            )
        except FusionPipelineNode.DoesNotExist:
            logger.warning(
                "[PipelineOrchestrator] ITERATE 目标节点未找到 target=%s pack=%s",
                target_node_id, node.pack_id,
            )
            return {
                "status": "error",
                "errors": [f"ITERATE 目标节点 {target_node_id} 不存在"],
            }

        iteration_results: List[Dict[str, Any]] = []
        prev_score: Optional[float] = None
        final_result: Optional[Dict[str, Any]] = None
        score_field = (until_condition or {}).get("field", "")

        for attempt in range(1, max_attempts + 1):
            try:
                result = self._run_serial_node(target_node)
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "[PipelineOrchestrator] ITERATE 第 %s 轮异常 target=%s: %s",
                    attempt, target_node_id, exc,
                )
                result = {"status": "failed", "errors": [str(exc)]}

            # 提取评分，用于评分提升收敛判定
            current_score: Optional[float] = None
            data = result.get("data") or result.get("outputs") or {}
            if isinstance(data, dict) and score_field:
                raw_score = data.get(score_field)
                if raw_score is not None:
                    try:
                        current_score = float(raw_score)
                    except (TypeError, ValueError):
                        current_score = None

            iteration_results.append({
                "attempt": attempt,
                "result": result,
                "score": current_score,
            })
            final_result = result

            # 收敛条件检查：满足用户配置条件立即终止
            if self._check_iterate_condition(target_node, result, until_condition):
                logger.info(
                    "[PipelineOrchestrator] ITERATE 满足终止条件 target=%s attempt=%s",
                    target_node_id, attempt,
                )
                break
            # 评分提升收敛：上次 vs 这次评分差 < 1 分也算达标
            if (
                prev_score is not None
                and current_score is not None
                and abs(current_score - prev_score) < 1.0
            ):
                logger.info(
                    "[PipelineOrchestrator] ITERATE 评分提升 <1 触发终止 target=%s attempt=%s",
                    target_node_id, attempt,
                )
                break

            prev_score = current_score

        final_status = (final_result or {}).get("status", "error")
        return {
            "status": "completed" if final_status == "completed" else "failed",
            "iterations": iteration_results,
            "max_attempts": max_attempts,
            "actual_attempts": len(iteration_results),
            "target_node_id": target_node_id,
        }

    def _check_iterate_condition(
        self,
        target_node: "FusionPipelinePack",
        result: Dict[str, Any],
        condition: Optional[Dict[str, Any]],
    ) -> bool:
        """
        检查 ITERATE 循环是否可终止。
        条件格式：{"field": "overall_score", "operator": ">=", "value": 70}
        """
        if not condition:
            return False  # 无条件时仅按 max_attempts 兜底

        field = condition.get("field", "")
        operator = condition.get("operator", ">=")
        value = condition.get("value")
        if not field or value is None:
            return False

        # 从 result.data 或 result.outputs 中读取字段值
        data = result.get("data") or result.get("outputs") or {}
        if not isinstance(data, dict):
            return False
        actual = data.get(field)
        if actual is None:
            return False

        try:
            actual_num = float(actual)
            value_num = float(value)
        except (TypeError, ValueError):
            return False

        if operator == ">=" and actual_num >= value_num:
            return True
        if operator == ">" and actual_num > value_num:
            return True
        if operator == "==" and actual_num == value_num:
            return True
        if operator == "<=" and actual_num <= value_num:
            return True
        if operator == "<" and actual_num < value_num:
            return True
        return False

    def _run_human_gate_node(self, node: "FusionPipelinePack", results: list) -> Dict[str, Any]:
        """
        HUMAN 节点：step 模式下暂停等待用户确认。

        仅在 project.pipeline_mode == "step" 时暂停；auto/workspace 模式自动通过。
        暂停时：标记 project.status=awaiting、广播 SSE awaiting_user 事件。
        """
        # auto / workspace 模式直接通过，避免阻塞流水线
        if self.project.pipeline_mode != Project.MODE_STEP:
            return {
                "status": "auto_skipped",
                "human_gate": node.fusion_node_id,
                "message": "非 step 模式，自动跳过人工门控",
            }

        # step 模式：标记项目为 awaiting
        try:
            self.project.status = Project.STATUS_AWAITING
            self.project.current_node_index = node.chain_order
            self.project.save(update_fields=["status", "current_node_index", "updated_at"])
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[PipelineOrchestrator] HUMAN 节点更新 project.status 失败: %s", exc,
            )

        # 广播 SSE 进度事件
        try:
            from apps.creation.services.sse_progress import broadcast_progress

            broadcast_progress(str(self.project.id), {
                "event": "awaiting_user",
                "project_id": str(self.project.id),
                "node_index": node.chain_order,
                "node_name": node.name,
                "message": "等待用户确认",
            })
        except ImportError:
            logger.debug("[PipelineOrchestrator] SSE broadcast 模块未找到，跳过")
        except Exception as exc:  # noqa: BLE001
            logger.warning("[PipelineOrchestrator] HUMAN 节点 SSE 广播失败: %s", exc)

        return {
            "status": "awaiting_user",
            "human_gate": node.fusion_node_id,
            "message": (node.extra_config or {}).get(
                "human_gate_message", "请确认当前节点产物后继续",
            ),
        }

    def _rollback_to_stable_node(self, last_stable_chain_order: int) -> None:
        """
        失败回滚：把 project.current_node_index 回退到上一个稳定节点。
        注意：仅回退索引，不删除已落库的 artifact（产物保留以供诊断）。
        """
        try:
            self.project.current_node_index = max(0, int(last_stable_chain_order))
            self.project.save(update_fields=["current_node_index", "updated_at"])
            logger.info(
                "[PipelineOrchestrator] 回滚到稳定节点 chain_order=%s project=%s",
                last_stable_chain_order, self.project.id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[PipelineOrchestrator] 失败回滚失败 project=%s: %s",
                self.project.id, exc,
            )

    def run_node(self, node: "FusionPipelinePack") -> Dict[str, Any]:
        """
        执行单个节点（公开入口，保持向后兼容）。
        内部委托给 _run_node 分发到对应 runner_type。
        """
        return self._run_node(node, results=[])

    def _invoke_agent(self, agent_id: str, node: "FusionPipelinePack") -> AgentResult:
        """调用 Agent 并写入执行记录。"""
        from apps.agent.runtime import resolve_agent_runner

        runner = resolve_agent_runner(agent_id)
        if not runner:
            return AgentResult(agent_id=agent_id, status="error", errors=[f"Agent runner 未配置: {agent_id}"])

        return AgentExecutionRunService.run_tracked_agent(
            self.project,
            agent_id,
            runner,
            node_index=node.website_index,
            input_summary={
                "pack_version": getattr(node.pack, "version", ""),
                "fusion_node_id": node.fusion_node_id,
            },
        )

    # -------------------------------------------------------------------------
    # 条件评估
    # -------------------------------------------------------------------------

    def evaluate_condition(self, node: "FusionPipelinePack") -> bool:
        """
        评估 CONDITION 节点的条件表达式。
        条件格式：{"field": "overall_score", "operator": ">=", "value": 70}
        从 project 或 artifact 读取 field 值，与 value 比较。
        """
        import operator

        # TODO: 从 node 读取条件配置（当前 node 结构中可能通过 extra_artifact_keys 或其他字段存储条件）
        condition = self._extract_condition_from_node(node)
        if not condition:
            return True  # 无条件默认通过

        field = condition.get("field", "")
        cond_op = condition.get("operator", "==")
        cond_value = condition.get("value")

        # 从 project 属性读取
        if hasattr(self.project, field):
            actual = getattr(self.project, field)
        else:
            # 从 artifact 读取
            from ..artifact_service import get_artifact

            artifact = get_artifact(self.project, field)
            actual = artifact.get(field) if isinstance(artifact, dict) else None

        if actual is None:
            logger.warning(
                "[PipelineOrchestrator] evaluate_condition 字段未找到 field=%s node=%s",
                field,
                node.fusion_node_id,
            )
            return False

        # 执行比较
        op_map = {
            ">=": operator.ge,
            "<=": operator.le,
            ">": operator.gt,
            "<": operator.lt,
            "==": operator.eq,
            "!=": operator.ne,
        }
        op_func = op_map.get(cond_op, operator.eq)
        try:
            return op_func(float(actual), float(cond_value))
        except (TypeError, ValueError):
            logger.warning(
                "[PipelineOrchestrator] evaluate_condition 比较失败 actual=%s cond=%s",
                actual,
                cond_value,
            )
            return False

    def _extract_condition_from_node(self, node: "FusionPipelinePack") -> Optional[Dict[str, Any]]:
        """从节点提取条件配置。"""
        # TODO: 实际从 node 的配置字段读取条件表达式
        # 临时通过 extra_artifact_keys[0] 作为条件 JSON
        extra = node.extra_artifact_keys
        if extra and isinstance(extra, list) and len(extra) > 0:
            try:
                return extra[0] if isinstance(extra[0], dict) else {}
            except (IndexError, TypeError):
                pass
        return None

    # -------------------------------------------------------------------------
    # 进度上报
    # -------------------------------------------------------------------------

    def broadcast_progress(
        self,
        node: "FusionPipelinePack",
        status: str,
        node_result: Dict[str, Any],
    ) -> None:
        """
        进度上报：写入 Project.current_node_index / progress_percent，
        并通过 SSE 广播。
        """
        node_index = node.website_index

        # 更新项目进度字段
        update_fields = ["current_node_index", "updated_at"]
        self.project.current_node_index = node_index

        # 计算进度百分比
        total = self.project.total_nodes or 1
        progress = min(100, int((node_index / total) * 100))
        self.project.progress_percent = progress

        if status == "error":
            self.project.error_message = "; ".join(
                str(e) for e in node_result.get("errors", [])
            )[:500]
            update_fields.append("error_message")

        self.project.save(update_fields=update_fields)

        # SSE 广播
        try:
            from apps.creation.services.sse_progress import broadcast_progress

            broadcast_progress(
                project_id=str(self.project.id),
                event_data={
                    "event": "node_progress",
                    "project_id": str(self.project.id),
                    "node_index": node_index,
                    "fusion_node_id": node.fusion_node_id,
                    "node_name": node.name,
                    "status": status,
                    "overall_progress": progress,
                    "result": node_result,
                },
            )
        except ImportError:
            logger.debug("[PipelineOrchestrator] SSE broadcast 模块未找到，跳过")
        except Exception as exc:  # noqa: BLE001
            logger.warning("[PipelineOrchestrator] SSE broadcast 失败: %s", exc)

    def _update_project_progress(self, completed: int, total: int) -> None:
        """更新项目整体进度。"""
        progress = min(100, int((completed / total) * 100)) if total > 0 else 0
        self.project.progress_percent = progress
        self.project.save(update_fields=["progress_percent", "updated_at"])

        # 更新当前节点索引
        if completed < total:
            self.project.current_node_index = completed + 1
            self.project.save(update_fields=["current_node_index", "updated_at"])

    def _run_external_api_node(self, node: "FusionPipelinePack", results: list) -> dict:
        """
        EXTERNAL 节点：调用外部 API（如视频生成 / 图像生成 / 第三方 AI 能力）。

        配置来自 node.extra_config：
        {
            "external_api_url": "https://api.example.com/video/generate",
            "external_api_method": "POST",
            "external_api_headers": {"Authorization": "Bearer ..."},
            "external_payload_template": {"prompt": "{{script_content}}"},
            "external_timeout_seconds": 120,
            "external_retry_attempts": 1,
            "external_result_field": "video_url"
        }
        """
        import re
        import requests

        config = node.extra_config or {}
        url = config.get("external_api_url")
        method = config.get("external_api_method", "POST").upper()
        headers = config.get("external_api_headers", {})
        timeout = config.get("external_timeout_seconds", 60)
        retry_attempts = config.get("external_retry_attempts", 1)
        result_field = config.get("external_result_field", "result")

        if not url:
            return {
                "status": "error",
                "error": "外部 API 节点缺少 external_api_url 配置",
                "node_id": node.fusion_node_id,
            }

        # 从 artifact 或 upstream context 获取请求体
        upstream_context = results[-1].get("data", {}) if results else {}
        payload = self._render_template(
            config.get("external_payload_template", {}),
            upstream_context
        )

        # 重试逻辑
        last_error = None
        for attempt in range(retry_attempts + 1):
            try:
                if method == "POST":
                    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
                else:
                    resp = requests.get(url, params=payload, headers=headers, timeout=timeout)
                resp.raise_for_status()
                result = resp.json()

                return {
                    "status": "completed",
                    "external_result": result.get(result_field),
                    "full_response": result,
                    "node_id": node.fusion_node_id,
                }
            except requests.exceptions.Timeout:
                last_error = f"请求超时（{timeout}s）"
                logger.warning(
                    "[PipelineOrchestrator] 外部 API 超时 node=%s attempt=%s/%s",
                    node.fusion_node_id, attempt + 1, retry_attempts + 1,
                )
            except requests.exceptions.HTTPError as exc:
                last_error = f"HTTP 错误：{exc.response.status_code}"
                logger.warning(
                    "[PipelineOrchestrator] 外部 API HTTP 错误 node=%s status=%s",
                    node.fusion_node_id, exc.response.status_code,
                )
            except Exception as exc:
                last_error = f"外部 API 调用失败：{exc}"
                logger.warning(
                    "[PipelineOrchestrator] 外部 API 异常 node=%s: %s",
                    node.fusion_node_id, exc,
                )

            if attempt < retry_attempts:
                import time
                time.sleep(min(2 ** attempt, 8))  # 指数退避，最多 8 秒

        return {
            "status": "failed",
            "error": last_error or "重试耗尽",
            "node_id": node.fusion_node_id,
        }

    def _render_template(self, template: dict, context: dict) -> dict:
        """
        简单的模板渲染：将 {{ field_name }} 占位符替换为 context 中的值。
        """
        def replace_field(obj):
            if isinstance(obj, str):
                return re.sub(
                    r'\{\{(\w+)\}\}',
                    lambda m: str(context.get(m.group(1), "")),
                    obj
                )
            elif isinstance(obj, dict):
                return {k: replace_field(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_field(item) for item in obj]
            return obj
        return replace_field(template)


# =============================================================================
# 模块级灰度切流函数
# =============================================================================


def resolve_pipeline_pack_for_project(project: Project) -> Optional["FusionPipelinePack"]:
    """
    为创作项目解析应该使用的工作流包。
    优先使用 project.pipeline_pack（如用户指定）；
    否则按 gray_traffic_salt + user_id % 100 自动灰度分流。
    返回 None 表示无可用工作流包。
    """
    return PipelineOrchestrator(project).resolve_pack()


def run_creation_pipeline(project: Project) -> Dict[str, Any]:
    """
    创作流水线主入口，供 tasks.py 调用。
    1. 解析 pack（resolve_pipeline_pack_for_project）
    2. 记录 gray_flow_version 到 project
    3. 执行 PipelineOrchestrator().run(pack)
    """
    from apps.workflow.models import FusionPipelinePack

    pack = resolve_pipeline_pack_for_project(project)
    if not pack:
        logger.warning("[Creation] 无可用工作流包 project=%s", project.id)
        return {"status": "failed", "results": [], "error": "无可用工作流包"}

    # 记录灰度版本到 project（用于追踪）
    gray_version = getattr(project, "gray_flow_version", None)
    if gray_version != pack.version:
        project.gray_flow_version = pack.version  # type: ignore
        try:
            project.save(update_fields=["gray_flow_version", "updated_at"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("[Creation] gray_flow_version 保存失败: %s", exc)

    # 执行流水线
    orchestrator = PipelineOrchestrator(project)
    return orchestrator.run(pack)
