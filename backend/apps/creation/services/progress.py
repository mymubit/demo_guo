"""创作进度查询与分步模式节点控制。"""

import logging
from datetime import timedelta
from typing import Optional

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.workflow.services.pipeline_service import WorkflowPipelineService

from ..models import CreationNode, DownloadToken, Project, ScriptWork
from ._helpers import _get_user_project
from ._rendering import _render_progress_html, _render_result_html

logger = logging.getLogger(__name__)


def get_progress(project_id: str, user) -> dict:
    """查询创作进度。"""
    project = _get_user_project(project_id, user)

    rendered_progress_html = _render_progress_html(project)

    download_token_str = ""
    if project.status == Project.STATUS_COMPLETED:
        try:
            dl = (
                DownloadToken.objects.filter(
                    project=project,
                    user=user,
                    file_format=ScriptWork.FORMAT_MARKDOWN,
                    is_used=False,
                    expires_at__gt=timezone.now(),
                )
                .order_by("-created_at")
                .first()
            )
            if dl is None:
                dl = DownloadToken.objects.create(
                    project=project,
                    user=user,
                    token=DownloadToken.generate_token(),
                    file_format=ScriptWork.FORMAT_MARKDOWN,
                    expires_at=timezone.now() + timedelta(minutes=15),
                )
            download_token_str = dl.token
        except Exception as exc:  # noqa: BLE001
            logger.warning("[Creation] 生成下载 token 失败: %s", exc)

    gate_summary = None
    try:
        from ..artifact_service import get_artifact
        from ..episode_gate import summarize_episode_gates

        scripts_art = get_artifact(project, "episode_scripts")
        if scripts_art:
            gate_summary = summarize_episode_gates(scripts_art)
    except Exception:  # noqa: BLE001
        pass

    score_summary = None
    if project.overall_score is not None or project.grade:
        score_summary = {
            "overallScore": project.overall_score,
            "grade": project.grade,
        }

    node_preview = None
    if project.status == Project.STATUS_AWAITING and project.current_node_index:
        try:
            from ..node_preview import build_node_preview

            node_preview = build_node_preview(project, project.current_node_index)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[Creation] 节点预览构建失败: %s", exc)

    completed_previews: list = []
    try:
        from ..node_preview import build_completed_node_previews

        completed_previews = build_completed_node_previews(project)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Creation] 已完成节点预览构建失败: %s", exc)

    node_meta = WorkflowPipelineService.node_meta_by_index()
    from ..step_mode import artifact_key_for_node

    excluded = WorkflowPipelineService.portal_hidden_fusion_node_ids()
    nodes_payload = []
    for n in project.nodes.all().order_by("node_index"):
        meta = node_meta.get(n.node_index, {})
        fid = n.fusion_node_id or meta.get("fusion_node_id") or ""
        if fid in excluded:
            continue
        nodes_payload.append(
            {
                "index": n.node_index,
                "fusion_node_id": n.fusion_node_id or meta.get("fusion_node_id"),
                "name": n.node_name or meta.get("name"),
                "description": meta.get("description") or "",
                "output_key": meta.get("output_key") or "",
                "sub_skill": meta.get("sub_skill") or "",
                "artifact_key": artifact_key_for_node(n.node_index) or "",
                "status": n.status,
                "status_text": n.get_status_display(),
                "summary": n.summary_text,
            }
        )

    is_queued = project.status == Project.STATUS_PENDING and not any(
        n["status"] == CreationNode.STATUS_RUNNING for n in nodes_payload
    )

    result = {
        "status": project.status,
        "status_text": project.get_status_display(),
        "fusion_status": project.fusion_status or "",
        "fusion_status_text": (
            dict(Project.FUSION_STATUS_CHOICES).get(project.fusion_status, "")
            if project.fusion_status
            else ""
        ),
        "overall_score": project.overall_score,
        "grade": project.grade,
        "ready_at": project.ready_at,
        "skill_version": project.skill_version,
        "score_summary": score_summary,
        "gate_summary": gate_summary,
        "pipeline_mode": project.pipeline_mode,
        "awaiting_confirm": project.status == Project.STATUS_AWAITING,
        "node_preview": node_preview,
        "completed_previews": completed_previews,
        "nodes": nodes_payload,
        "current_node": project.current_node_index,
        "total_nodes": project.total_nodes,
        "progress_percent": project.progress_percent,
        "is_queued": is_queued,
        "rendered_progress_html": rendered_progress_html,
        "rendered_result_html": (
            _render_result_html(project)
            if project.status == Project.STATUS_COMPLETED
            else ""
        ),
        "download_token": download_token_str,
        "error_message": project.error_message if project.status == Project.STATUS_FAILED else "",
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
    return result


@transaction.atomic
def confirm_node(project_id: str, user) -> Project:
    """确认当前节点产物，继续下一节点。"""
    from ..step_mode import next_node_index
    from ..tasks import run_creation_step
    from dj_queue.api import enqueue_on_commit

    project = _get_user_project(project_id, user)
    if project.pipeline_mode != Project.MODE_STEP:
        raise PermissionDenied("仅分步模式可手动确认节点")
    if project.status != Project.STATUS_AWAITING:
        raise PermissionDenied("当前不在待确认状态")
    from apps.workflow.services.flow_graph_service import FlowGraphPlanService

    pending = FlowGraphPlanService.pending_parallel_indices(project, project.current_node_index)
    nxt = (
        pending[0]
        if pending
        else FlowGraphPlanService.next_node_index_for_project(project, project.current_node_index)
    )
    if nxt is None:
        raise PermissionDenied("主链节点已全部完成")
    project.status = Project.STATUS_PENDING
    project.save(update_fields=["status", "updated_at"])
    enqueue_on_commit(run_creation_step, str(project.id), nxt)
    logger.info("[Creation] 用户确认节点 %s → %s project=%s", project.current_node_index, nxt, project.id)
    return project


@transaction.atomic
def regenerate_node(project_id: str, user, node_index: Optional[int] = None) -> Project:
    """重新执行指定节点（默认当前待确认节点）。"""
    from ..step_mode import clear_artifacts_from_node, reset_nodes_from_index
    from ..tasks import run_creation_step
    from dj_queue.api import enqueue_on_commit

    project = _get_user_project(project_id, user)
    if project.pipeline_mode != Project.MODE_STEP:
        raise PermissionDenied("仅分步模式可重跑节点")
    idx = int(node_index or project.current_node_index)
    if idx < 1 or idx > 7:
        raise PermissionDenied("无效的节点索引")
    if project.status == Project.STATUS_RUNNING:
        raise PermissionDenied("节点执行中，请稍候")
    clear_artifacts_from_node(project, idx)
    reset_nodes_from_index(project, idx)
    project.status = Project.STATUS_PENDING
    project.error_message = ""
    project.overall_score = None
    project.grade = ""
    project.ready_at = None
    project.save(
        update_fields=[
            "status",
            "error_message",
            "overall_score",
            "grade",
            "ready_at",
            "updated_at",
        ]
    )
    enqueue_on_commit(run_creation_step, str(project.id), idx)
    logger.info("[Creation] 重跑节点 %s project=%s", idx, project.id)
    return project
