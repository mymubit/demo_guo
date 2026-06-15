# -*- coding: utf-8 -*-
"""AgentOrchestrator：统一调度入口。"""
from __future__ import annotations

import logging
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
