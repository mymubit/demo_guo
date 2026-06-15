# -*- coding: utf-8 -*-
"""分步创作模式：单节点执行、确认、重跑。"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from apps.workflow.services.pipeline_service import WorkflowPipelineService
from apps.common.user_messages import safe_api_message
from apps.workflow.fusion import FusionNodeRegistry, get_artifact_registry
from django.utils.module_loading import import_string

from .artifact_renderer import episode_scripts_to_legacy_scripts
from .artifact_service import get_artifact
from .models import CreationNode, Project, ProjectFusionArtifact
from .services import _render_progress_html, refresh_project_progress

logger = logging.getLogger(__name__)

_artifact_reg = get_artifact_registry()
_STEP_RUNNER_IMPORT_PREFIX = "apps.creation."
_RUNNER_PATH_BY_TYPE = {
    "fusion_node": "apps.creation.step_mode.run_orchestrator_step",
    "fusion_review": "apps.creation.step_mode.run_fusion_review_step",
    "fusion_score": "apps.creation.step_mode.run_fusion_score_step",
}


def artifact_key_for_node(node_index: int) -> Optional[str]:
    return _artifact_reg.artifact_key_for_index(node_index)


def artifacts_for_node(node_index: int) -> List[str]:
    return _artifact_reg.artifacts_for_node(node_index)


# 向后兼容
ARTIFACTS_BY_NODE = {i: _artifact_reg.artifacts_for_node(i) for i in range(1, _artifact_reg.max_node_index() + 1)}
NODE_ARTIFACT_KEYS = {
    i: _artifact_reg.artifact_key_for_index(i)
    for i in range(1, _artifact_reg.max_node_index() + 1)
    if _artifact_reg.artifact_key_for_index(i)
}


def fusion_node_id_for_index(node_index: int) -> Optional[str]:
    return FusionNodeRegistry().fusion_node_id_for_index(node_index)


def runner_type_for_node(node_index: int) -> str:
    runner_type = FusionNodeRegistry().runner_type_for_index(node_index)
    if runner_type:
        return runner_type
    if int(node_index) <= 5:
        return "fusion_node"
    if int(node_index) == 6:
        return "fusion_review"
    if int(node_index) == 7:
        return "fusion_score"
    return ""


def runner_path_for_node(node_index: int) -> str:
    registry = FusionNodeRegistry()
    runner_path = registry.runner_path_for_index(node_index)
    if runner_path:
        return runner_path
    return _RUNNER_PATH_BY_TYPE.get(runner_type_for_node(node_index), "")


def resolve_step_runner(node_index: int) -> Optional[Callable[[Project, int], Dict[str, Any]]]:
    runner_path = runner_path_for_node(node_index)
    if not runner_path:
        return None
    if not runner_path.startswith(_STEP_RUNNER_IMPORT_PREFIX):
        logger.warning("[StepMode] runner path rejected node=%s path=%s", node_index, runner_path)
        return None
    try:
        return import_string(runner_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[StepMode] runner import failed node=%s path=%s err=%s", node_index, runner_path, exc)
        return None


def next_node_index(current: int) -> Optional[int]:
    return WorkflowPipelineService.creation_next_node_index(current)


def clear_artifacts_from_node(project: Project, from_index: int) -> None:
    keys = _artifact_reg.all_artifact_keys_from_index(from_index)
    if keys:
        ProjectFusionArtifact.objects.filter(
            project=project, artifact_key__in=keys
        ).delete()


def reset_nodes_from_index(project: Project, from_index: int) -> None:
    now_fields = {
        "status": CreationNode.STATUS_PENDING,
        "summary_text": "",
        "error_message": "",
        "completed_at": None,
        "started_at": None,
    }
    CreationNode.objects.filter(
        project=project, node_index__gte=from_index
    ).update(**now_fields)


def build_pipeline_result_from_project(project: Project) -> Dict[str, Any]:
    registry = get_artifact_registry()
    artifacts: Dict[str, Any] = {}
    result: Dict[str, Any] = {
        "status": "completed",
        "review": {},
        "artifacts": artifacts,
    }
    for source in registry.pipeline_result_sources():
        artifact_key = source["artifact_key"]
        pipeline_key = source["pipeline_result_key"]
        payload = get_artifact(project, artifact_key) or {}
        artifacts[artifact_key] = payload
        if registry.uses_legacy_script_transform(pipeline_key):
            result[pipeline_key] = (
                episode_scripts_to_legacy_scripts(payload) if payload else {}
            )
        else:
            result[pipeline_key] = payload
    for legacy_key in ("project_brief", "structure", "characters", "outlines", "scripts"):
        result.setdefault(legacy_key, {})
    return result


def node_requires_confirm(node_index: int) -> bool:
    meta = WorkflowPipelineService.node_meta_by_index().get(node_index) or {}
    return bool(meta.get("requires_confirm", True))


def mark_project_awaiting(project: Project, node_index: int) -> None:
    project.status = Project.STATUS_AWAITING
    project.current_node_index = node_index
    total = max(1, project.total_nodes or WorkflowPipelineService.creation_max_node_index())
    project.progress_percent = min(99, int(node_index / total * 100))
    project.rendered_progress_html = _render_progress_html(project)
    project.save(
        update_fields=[
            "status",
            "current_node_index",
            "progress_percent",
            "rendered_progress_html",
            "updated_at",
        ]
    )


def run_orchestrator_step(project: Project, node_index: int) -> Dict[str, Any]:
    from .orchestration.orchestrator import run_pipeline_step_by_index

    return run_pipeline_step_by_index(project, node_index)


def run_fusion_review_step(project: Project, node_index: int) -> Dict[str, Any]:
    from .orchestration.orchestrator import AgentOrchestrator, agent_result_to_fusion_post_step
    from apps.agent.runtime import agent_for_pipeline_node_index

    agent_id = agent_for_pipeline_node_index(int(node_index)) or "review"
    result = AgentOrchestrator(project).invoke(agent_id)
    return agent_result_to_fusion_post_step(result, int(node_index))


def run_fusion_score_step(project: Project, node_index: int) -> Dict[str, Any]:
    from .orchestration.orchestrator import AgentOrchestrator, agent_result_to_fusion_post_step
    from apps.agent.runtime import agent_for_pipeline_node_index

    agent_id = agent_for_pipeline_node_index(int(node_index)) or "score"
    result = AgentOrchestrator(project).invoke(agent_id)
    return agent_result_to_fusion_post_step(result, int(node_index))


def run_fusion_step(project: Project, node_index: int, runner_type: Optional[str] = None) -> Dict[str, Any]:
    runner = runner_type or runner_type_for_node(node_index)
    if runner == "fusion_review":
        return run_fusion_review_step(project, node_index)
    if runner == "fusion_score":
        return run_fusion_score_step(project, node_index)
    raise ValueError(f"节点 {node_index} 未配置融合后处理 runner")


def charge_node_success(project: Project, node_index: int) -> None:
    from apps.billing.services import BillingService, InsufficientCoins

    try:
        BillingService.charge_node(
            project.user,
            node_index,
            reference_id=f"{project.id}:n{node_index}",
        )
    except InsufficientCoins as exc:
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied(str(exc)) from exc


def _ensure_node_enabled(node_index: int) -> None:
    if not WorkflowPipelineService.is_node_enabled(node_index):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied(f"节点 {node_index} 已由运营关闭")


def execute_step(project: Project, node_index: int) -> Dict[str, Any]:
    """执行单个主链节点。"""
    max_idx = WorkflowPipelineService.creation_max_node_index()
    if node_index < 1 or node_index > max_idx:
        raise ValueError(f"node_index 必须在 1–{max_idx}")

    _ensure_node_enabled(node_index)

    project.status = Project.STATUS_RUNNING
    project.current_node_index = node_index
    project.error_message = ""
    project.save(update_fields=["status", "current_node_index", "error_message", "updated_at"])

    runner_type = runner_type_for_node(node_index)
    runner = resolve_step_runner(node_index)
    if not runner:
        return {"status": "error", "errors": [f"节点 {node_index} 未配置可执行 runner_path"]}

    out = runner(project, node_index)
    if out.get("status") == "error":
        return out
    if runner_type in {"fusion_review", "fusion_score"}:
        if not out.get("ok") and not out.get("skipped"):
            err = out.get("error") or "融合后处理失败"
            return {"status": "error", "errors": [err]}

    try:
        charge_node_success(project, node_index)
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "errors": [safe_api_message(exc, "扣费或权限校验失败")]}

    project.refresh_from_db()
    if project.pipeline_mode == Project.MODE_STEP and node_index < max_idx:
        if node_requires_confirm(node_index):
            mark_project_awaiting(project, node_index)
            return {"status": "awaiting", "node_index": node_index}
        next_idx = next_node_index(node_index)
        if next_idx:
            return execute_step(project, next_idx)

    return {"status": "step_done", "node_index": node_index, **(out or {})}
