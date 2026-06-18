# -*- coding: utf-8 -*-
"""项目执行态推导（替代已删除的 Project.status 列）。"""
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
    return AgentExecutionRun.objects.filter(
        project_id=project.id,
        status=AgentExecutionRun.STATUS_RUNNING,
    ).exists()


def derive_execution_status(project: Project) -> str:
    """根据 Agent run 与产物推导 legacy 执行态（pending/running/completed/failed/awaiting）。"""
    if _project_has_running_run(project):
        return Project.STATUS_RUNNING
    if _project_has_scripts(project):
        return Project.STATUS_COMPLETED
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
    if (
        project.pipeline_mode == Project.MODE_STEP
        and project.fusion_status == Project.FUSION_REVIEWING
    ):
        return Project.STATUS_AWAITING
    return Project.STATUS_PENDING


def filter_projects_by_execution_status(qs: QuerySet, status: str) -> QuerySet:
    """按推导执行态过滤 QuerySet（无 status 列时使用）。"""
    if not status:
        return qs
    running_ids = AgentExecutionRun.objects.filter(
        status=AgentExecutionRun.STATUS_RUNNING
    ).values("project_id")
    script_ids = ProjectFusionArtifact.objects.filter(
        artifact_key="episode_scripts"
    ).values("project_id")
    failed_ids = AgentExecutionRun.objects.filter(
        status=AgentExecutionRun.STATUS_FAILED
    ).values("project_id")

    if status == Project.STATUS_RUNNING:
        return qs.filter(id__in=running_ids)
    if status == Project.STATUS_COMPLETED:
        return qs.filter(id__in=script_ids)
    if status == Project.STATUS_FAILED:
        return qs.filter(fusion_status=Project.FUSION_BLOCKED) | qs.filter(
            id__in=failed_ids
        ).exclude(id__in=script_ids)
    if status == Project.STATUS_AWAITING:
        return qs.filter(
            pipeline_mode=Project.MODE_STEP,
            fusion_status=Project.FUSION_REVIEWING,
        ).exclude(id__in=running_ids)
    if status == Project.STATUS_PENDING:
        return (
            qs.exclude(id__in=running_ids)
            .exclude(id__in=script_ids)
            .exclude(fusion_status=Project.FUSION_BLOCKED)
            .exclude(
                pipeline_mode=Project.MODE_STEP,
                fusion_status=Project.FUSION_REVIEWING,
            )
        )
    return qs


def annotate_execution_busy(qs: QuerySet) -> QuerySet:
    """为 QuerySet 标注是否存在 running run（供批量判断）。"""
    running = AgentExecutionRun.objects.filter(
        project_id=OuterRef("pk"),
        status=AgentExecutionRun.STATUS_RUNNING,
    )
    return qs.annotate(_has_running_run=Exists(running))
