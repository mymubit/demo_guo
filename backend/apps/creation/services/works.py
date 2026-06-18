"""作品列表、详情、删除与 Agent 操作。"""

import logging
from typing import Optional

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q

from ..models import Project
from ._helpers import _get_user_project
from ._rendering import _render_progress_html, _render_result_html
from .content_quality import record_user_edit

logger = logging.getLogger(__name__)


def get_project_detail(project_id: str, user) -> dict:
    """获取作品详情（与 progress 类似，仅用于作品详情页）。"""
    project = _get_user_project(project_id, user)
    detail = {
        "project_id": str(project.id),
        "title": project.title,
        "theme": project.theme,
        "episode_count": project.episode_count,
        "format_variant": project.format_variant,
        "target_platform": project.target_platform,
        "status": project.status,
        "status_text": project.get_status_display(),
        "progress_percent": project.progress_percent,
        "audience": project.audience,
        "reference_work": project.reference_work,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "completed_at": project.completed_at,
        "fusion_status": project.fusion_status,
        "overall_score": project.overall_score,
        "grade": project.grade,
        "ready_at": project.ready_at,
        "skill_version": project.skill_version,
        "rendered_result_html": _render_result_html(project),
        "rendered_progress_html": _render_progress_html(project),
        "fusion_snapshot": None,
    }
    try:
        from ..node_preview import build_portal_fusion_snapshot

        detail["fusion_snapshot"] = build_portal_fusion_snapshot(project)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Creation] fusion_snapshot 构建失败: %s", exc)
    return detail


def list_user_projects(
    user,
    status_filter: Optional[str] = None,
    *,
    keyword: str = "",
    ordering: str = "-created_at",
):
    """获取用户的创作作品列表。"""
    qs = Project.objects.filter(user=user).only(
        "id", "title", "theme", "episode_count", "format_variant",
        "status", "progress_percent", "fusion_status", "overall_score",
        "grade", "ready_at", "created_at", "updated_at", "core_idea",
        "pipeline_mode", "creation_entry",
    )
    if status_filter and status_filter in {
        Project.STATUS_PENDING,
        Project.STATUS_RUNNING,
        Project.STATUS_AWAITING,
        Project.STATUS_COMPLETED,
        Project.STATUS_FAILED,
    }:
        qs = qs.filter(status=status_filter)
    keyword = (keyword or "").strip()
    if keyword:
        qs = qs.filter(Q(title__icontains=keyword) | Q(core_idea__icontains=keyword))
    ordering_map = {
        "newest": "-created_at",
        "score": "-overall_score",
        "episodes": "-episode_count",
        "-created_at": "-created_at",
    }
    qs = qs.order_by(ordering_map.get(ordering, "-created_at"))
    return qs


def _reconcile_project_running_state(
    project: Project,
    *,
    aggressive: bool = False,
) -> Project:
    """解除工作台遗留 running 锁（Worker 异常退出或事务污染后）。"""
    if project.pipeline_mode != Project.MODE_WORKSPACE:
        return project
    if project.status != Project.STATUS_RUNNING:
        return project
    from ..agent_runtime.independent_service import IndependentAgentService
    from ..models import AgentExecutionRun

    stale_override = 0 if aggressive else None
    running = AgentExecutionRun.objects.filter(
        project=project,
        status=AgentExecutionRun.STATUS_RUNNING,
    )
    for run in running:
        if stale_override is not None:
            run.status = AgentExecutionRun.STATUS_FAILED
            run.error_message = "管理员操作前强制解除 running 锁"
            run.save(update_fields=["status", "error_message", "updated_at"])
        else:
            IndependentAgentService.running_run(project)
    IndependentAgentService.update_project_status(project)
    project.refresh_from_db()
    return project


@transaction.atomic
def delete_user_project(project_id: str, user) -> dict:
    """删除用户作品（级联移除节点、产物、剧本文件与分享链接，不可恢复）。"""
    project = _get_user_project(project_id, user)
    project = _reconcile_project_running_state(project, aggressive=True)
    if project.status == Project.STATUS_RUNNING:
        raise PermissionDenied("创作进行中，请等待完成或失败后再删除")
    title = (project.title or "")[:200]
    project.delete()
    return {"project_id": str(project_id), "title": title, "deleted": True}


@transaction.atomic
def admin_delete_project(project_id: str) -> dict:
    """运营后台删除创作项目（级联删除，不可恢复）。"""
    try:
        project = Project.objects.select_for_update().get(pk=project_id)
    except Project.DoesNotExist:
        raise PermissionDenied("项目不存在")
    project = _reconcile_project_running_state(project, aggressive=True)
    if project.status == Project.STATUS_RUNNING:
        raise PermissionDenied("创作进行中，请等待完成或失败后再删除")
    title = (project.title or project.theme or "未命名")[:200]
    project.delete()
    return {"project_id": str(project_id), "title": title, "deleted": True}


def apply_work_polish(
    project_id: str,
    user,
    *,
    indices: Optional[list] = None,
    apply_all: bool = False,
    patch_script_fields: bool = False,
) -> dict:
    """作品页：用户确认后应用润色建议。"""
    project = _get_user_project(project_id, user)
    from ..polish_apply import apply_polish_suggestions

    try:
        return apply_polish_suggestions(
            project,
            indices=[int(i) for i in (indices or [])],
            apply_all=bool(apply_all),
            patch_script_fields=bool(patch_script_fields),
        )
    except ValueError as exc:
        raise PermissionDenied(str(exc)) from exc
