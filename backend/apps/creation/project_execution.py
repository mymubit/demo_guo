# -*- coding: utf-8 -*-
"""项目执行态推导（Drama SSOT）。"""
from __future__ import annotations

from django.db.models import Exists, OuterRef, Q, QuerySet

from .artifact_service import get_artifact
from .models import AgentExecutionRun, Project, ProjectFusionArtifact


def _project_has_scripts(project: Project) -> bool:
    if get_artifact(project, "episode_scripts"):
        return True
    return ProjectFusionArtifact.objects.filter(
        project_id=project.id, artifact_key="episode_scripts"
    ).exists()


def _project_has_running_run(project: Project) -> bool:
    if AgentExecutionRun.objects.filter(
        project_id=project.id,
        status=AgentExecutionRun.STATUS_RUNNING,
    ).exists():
        return True
    try:
        from apps.drama.models import DramaProject, DramaRoleExecution

        drama = DramaProject.objects.filter(project_id=project.id).first()
        if drama:
            return DramaRoleExecution.objects.filter(
                drama_project=drama,
                status=DramaRoleExecution.Status.RUNNING,
            ).exists()
    except Exception:  # noqa: BLE001
        pass
    return False


def _drama_awaiting_review(project: Project) -> bool:
    try:
        from apps.drama.models import DramaProject
        from apps.drama.progress_service import DramaProjectProgressService

        drama = DramaProjectProgressService.find_drama_project(project.id)
        if drama and drama.current_stage == DramaProject.Stage.REVIEW:
            return True
    except Exception:  # noqa: BLE001
        pass
    return False


def derive_execution_status(project: Project) -> str:
    """根据 Drama 运行态与产物推导执行态。"""
    if _project_has_running_run(project):
        return Project.STATUS_RUNNING
    if _project_has_scripts(project):
        return Project.STATUS_COMPLETED
    try:
        from apps.drama.progress_service import DramaProjectProgressService

        if DramaProjectProgressService.is_deliverable(project):
            return Project.STATUS_COMPLETED
        if DramaProjectProgressService.has_blocking_failure(project):
            return Project.STATUS_FAILED
    except Exception:  # noqa: BLE001
        pass
    latest_failed = (
        AgentExecutionRun.objects.filter(
            project_id=project.id,
            status=AgentExecutionRun.STATUS_FAILED,
        )
        .order_by("-finished_at", "-started_at")
        .first()
    )
    if latest_failed and not _project_has_scripts(project):
        return Project.STATUS_FAILED
    if _drama_awaiting_review(project):
        return Project.STATUS_AWAITING
    return Project.STATUS_PENDING


def filter_projects_by_execution_status(qs: QuerySet, status: str) -> QuerySet:
    """按推导执行态过滤 QuerySet。"""
    if not status:
        return qs

    from apps.drama.progress_service import DramaProjectProgressService

    running_ids = list(DramaProjectProgressService.in_progress_project_ids())
    if not running_ids:
        running_ids = list(
            AgentExecutionRun.objects.filter(
                status=AgentExecutionRun.STATUS_RUNNING
            ).values_list("project_id", flat=True)
        )
    script_ids = ProjectFusionArtifact.objects.filter(
        artifact_key="episode_scripts"
    ).values_list("project_id", flat=True)
    deliverable_ids = DramaProjectProgressService.deliverable_project_ids()
    blocked_ids = DramaProjectProgressService.blocked_project_ids()
    failed_ids = AgentExecutionRun.objects.filter(
        status=AgentExecutionRun.STATUS_FAILED
    ).values_list("project_id", flat=True)

    if status == Project.STATUS_RUNNING:
        return qs.filter(id__in=running_ids)
    if status == Project.STATUS_COMPLETED:
        return qs.filter(id__in=deliverable_ids) | qs.filter(id__in=script_ids)
    if status == Project.STATUS_FAILED:
        return qs.filter(id__in=blocked_ids) | qs.filter(id__in=failed_ids).exclude(
            id__in=script_ids
        ).exclude(id__in=deliverable_ids)
    if status == Project.STATUS_AWAITING:
        from apps.drama.models import DramaProject

        review_pids = DramaProject.objects.filter(
            current_stage=DramaProject.Stage.REVIEW
        ).values_list("project_id", flat=True)
        return qs.filter(id__in=review_pids).exclude(id__in=running_ids)
    if status == Project.STATUS_PENDING:
        from apps.drama.models import DramaProject

        review_pids = DramaProject.objects.filter(
            current_stage=DramaProject.Stage.REVIEW
        ).values_list("project_id", flat=True)
        return (
            qs.exclude(id__in=running_ids)
            .exclude(id__in=script_ids)
            .exclude(id__in=deliverable_ids)
            .exclude(id__in=blocked_ids)
            .exclude(id__in=review_pids)
        )
    return qs


def annotate_execution_busy(qs: QuerySet) -> QuerySet:
    """为 QuerySet 标注是否存在 running run。"""
    running = AgentExecutionRun.objects.filter(
        project_id=OuterRef("pk"),
        status=AgentExecutionRun.STATUS_RUNNING,
    )
    return qs.annotate(_has_running_run=Exists(running))
