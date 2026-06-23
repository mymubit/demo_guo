# -*- coding: utf-8 -*-
"""??????????? Agent ???"""

import logging
from datetime import timedelta
from typing import Optional

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..models import Project
from ..admin_status import resolve_admin_status
from ._helpers import _get_user_project
from ._rendering import _render_progress_html, _render_result_html
from .content_quality import record_user_edit

logger = logging.getLogger(__name__)


def get_project_detail(project_id: str, user) -> dict:
    """???????? progress ?????????????"""
    project = _get_user_project(project_id, user)
    status, status_text = resolve_admin_status(project)
    detail = {
        "project_id": str(project.id),
        "title": project.title,
        "theme": project.theme,
        "episode_count": project.episode_count,
        "format_variant": project.format_variant,
        "target_platform": project.target_platform,
        "status": status,
        "status_text": status_text,
        "progress_percent": project.progress_percent,
        "audience": project.audience,
        "reference_work": project.reference_work,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "completed_at": project.completed_at,
        "overall_score": project.overall_score,
        "grade": project.grade,
        "ready_at": project.ready_at,
        "skill_version": project.skill_version,
        "result_html": _render_result_html(project),
        "progress_html": _render_progress_html(project),
        "fusion_snapshot": None,
    }
    try:
        from ..artifact_service import build_fusion_snapshot

        detail["fusion_snapshot"] = build_fusion_snapshot(project)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Creation] fusion_snapshot ????: %s", exc)
    return detail


def list_user_projects(
    user,
    status_filter: Optional[str] = None,
    *,
    keyword: str = "",
    ordering: str = "-created_at",
    scope: str = "",
):
    """????????????

    scope=drama???? Drama ??????track_mode ? fast/expert??
    """
    qs = Project.objects.filter(user=user).only(
        "id", "title", "theme", "episode_count", "format_variant",
        "progress_percent", "overall_score",
        "grade", "ready_at", "created_at", "updated_at", "core_idea",
        "pipeline_mode", "creation_entry",
    )
    scope = (scope or "").strip().lower()
    if scope == "drama":
        from apps.drama.constants import DramaTrackMode

        qs = qs.filter(track_mode__in=[DramaTrackMode.FAST, DramaTrackMode.EXPERT])
    if status_filter and status_filter in {
        Project.STATUS_PENDING,
        Project.STATUS_RUNNING,
        Project.STATUS_AWAITING,
        Project.STATUS_COMPLETED,
        Project.STATUS_FAILED,
    }:
        from ..project_execution import filter_projects_by_execution_status

        qs = filter_projects_by_execution_status(qs, status_filter)
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


def build_user_work_list_page(
    user,
    *,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    keyword: str = "",
    ordering: str = "newest",
    scope: str = "",
) -> dict:
    """????????????? / ?????????"""
    from apps.creation.serializers import ProjectListSerializer

    qs = list_user_projects(
        user,
        status_filter,
        keyword=keyword,
        ordering=ordering,
        scope=scope,
    )
    total = qs.count()
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    start = (page - 1) * page_size
    items_qs = list(qs[start : start + page_size])

    for project in items_qs:
        if (
            project.pipeline_mode == Project.MODE_WORKSPACE
            and project.execution_status == Project.STATUS_RUNNING
        ):
            _reconcile_project_running_state(project)

    items = ProjectListSerializer(
        instance=items_qs,
        many=True,
    )
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "items": items.data,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    }


def _reconcile_project_running_state(
    project: Project,
    *,
    aggressive: bool = False,
) -> Project:
    """???? running ??Worker ????????????"""
    from ..models import AgentExecutionRun

    if aggressive:
        AgentExecutionRun.objects.filter(
            project=project,
            status=AgentExecutionRun.STATUS_RUNNING,
        ).update(
            status=AgentExecutionRun.STATUS_FAILED,
            error_message="?????????? running ?",
        )
        try:
            from apps.drama.models import DramaRoleExecution

            DramaRoleExecution.objects.filter(
                project=project,
                status=DramaRoleExecution.Status.RUNNING,
            ).update(
                status=DramaRoleExecution.Status.FAILED,
                error_message="?????????? running ?",
            )
        except Exception:  # noqa: BLE001
            pass
        if project.pipeline_mode == Project.MODE_WORKSPACE:
            from ..agent_runtime.independent_service import IndependentAgentService

            IndependentAgentService.update_project_status(project)
        project.refresh_from_db()
        return project

    if project.pipeline_mode != Project.MODE_WORKSPACE:
        return project
    if project.execution_status != Project.STATUS_RUNNING:
        return project
    from ..agent_runtime.independent_service import IndependentAgentService

    running = AgentExecutionRun.objects.filter(
        project=project,
        status=AgentExecutionRun.STATUS_RUNNING,
    )
    for run in running:
        IndependentAgentService.running_run(project)
    IndependentAgentService.update_project_status(project)
    project.refresh_from_db()
    return project


def _fail_stale_running(project: Project) -> Project:
    """Worker ???????? running ?? stale ??????"""
    try:
        from apps.drama.services import DramaRoleRunService

        DramaRoleRunService.fail_stale_active_executions(project)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Creation] fail_stale_active_executions failed: %s", exc)
    return project


@transaction.atomic
def delete_user_project(project_id: str, user) -> dict:
    """?????????????????????????????????"""
    project = _get_user_project(project_id, user)
    project = _fail_stale_running(project)
    project = _reconcile_project_running_state(project, aggressive=False)
    if project.execution_status == Project.STATUS_RUNNING:
        raise PermissionDenied("??????????????????")
    title = (project.title or "")[:200]
    project.delete()
    return {"project_id": str(project_id), "title": title, "deleted": True}


@transaction.atomic
def admin_delete_project(project_id: str) -> dict:
    """??????????????????????"""
    try:
        project = Project.objects.select_for_update().get(pk=project_id)
    except Project.DoesNotExist:
        raise PermissionDenied("?????")
    project = _fail_stale_running(project)
    project = _reconcile_project_running_state(project, aggressive=False)
    if project.execution_status == Project.STATUS_RUNNING:
        raise PermissionDenied("??????????????????")
    title = (project.title or project.theme or "???")[:200]
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
    """????????????????"""
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
