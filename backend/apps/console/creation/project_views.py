# -*- coding: utf-8 -*-
"""后台：创作项目运营列表与 Agent 观测摘要。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.creation.artifact_service import get_artifact
from apps.creation.models import Project, ProjectFusionArtifact
from apps.creation.services import CreationService
from apps.creation.workspace.workspace_service import _verify_summary

from apps.console.orchestration.execution_views import aggregate_sub_skill_stats
from apps.console.responses import api_fail, api_ok


def _batch_artifact_map(project_ids: List[UUID]) -> Dict[UUID, Dict[str, Any]]:
    if not project_ids:
        return {}
    rows = ProjectFusionArtifact.objects.filter(
        project_id__in=project_ids,
        artifact_key__in=("adaptation_meta", "agent_execution_traces"),
    )
    out: Dict[UUID, Dict[str, Any]] = {}
    for row in rows:
        bucket = out.setdefault(row.project_id, {})
        bucket[row.artifact_key] = row.payload if isinstance(row.payload, dict) else {}
    return out


def _project_ops_row(
    project: Project,
    artifacts: Optional[Dict[str, Any]] = None,
    execution_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    artifacts = artifacts or {}
    adaptation = artifacts.get("adaptation_meta") or get_artifact(project, "adaptation_meta") or {}
    traces = artifacts.get("agent_execution_traces") or get_artifact(project, "agent_execution_traces") or {}
    verify = _verify_summary(adaptation) if adaptation else {"hasReports": False, "allPassed": True, "stages": []}
    user = project.user
    exec_summary = execution_summary or {}
    row = {
        "project_id": str(project.id),
        "title": (project.title or project.theme or "未命名")[:200],
        "theme": project.theme,
        "status": project.status,
        "status_text": project.get_status_display(),
        "pipeline_mode": project.pipeline_mode,
        "creation_entry": project.creation_entry or "from-scratch",
        "fusion_status": project.fusion_status or "",
        "overall_score": project.overall_score,
        "grade": project.grade or "",
        "progress_percent": project.progress_percent,
        "episode_count": project.episode_count,
        "user_id": str(user_id) if (user_id := getattr(user, "id", None)) else "",
        "user_phone": getattr(user, "phone", "") or "",
        "has_agent_traces": bool(traces),
        "trace_agent_count": len(traces) if isinstance(traces, dict) else 0,
        "verify_summary": verify,
        "created_at": project.created_at.isoformat() if project.created_at else "",
        "updated_at": project.updated_at.isoformat() if project.updated_at else "",
        "execution_run_count": exec_summary.get("run_count", 0),
        "execution_failed_count": exec_summary.get("failed_count", 0),
        "latest_execution_run": exec_summary.get("latest_run"),
        "latest_failed_run": exec_summary.get("latest_failed_run"),
    }
    return row


def build_creation_ops_alerts() -> Dict[str, int]:
    """Dashboard / 创作中心待办计数。"""
    from apps.creation.models import AgentExecutionRun

    failed_project_ids = AgentExecutionRun.objects.filter(
        status=AgentExecutionRun.STATUS_FAILED
    ).values("project_id")
    return {
        "running": Project.objects.filter(status=Project.STATUS_RUNNING).count(),
        "failed": Project.objects.filter(status=Project.STATUS_FAILED).count(),
        "awaiting": Project.objects.filter(status=Project.STATUS_AWAITING).count(),
        "pending": Project.objects.filter(status=Project.STATUS_PENDING).count(),
        "has_failed_run": Project.objects.filter(id__in=failed_project_ids).count(),
    }


def build_agent_ops_dashboard(*, stats_limit: int = 200) -> Dict[str, Any]:
    """Dashboard Agent 运营摘要。"""
    from apps.agent.runtime import get_agent_registry
    from apps.creation.monitoring.execution_run_service import AgentExecutionRunService

    registry = get_agent_registry()
    stats = aggregate_sub_skill_stats(limit=stats_limit)
    top_skills = (stats.get("skills") or [])[:6]
    execution = AgentExecutionRunService.dashboard_payload(days=30)
    return {
        "registry_version": (registry.get("_meta") or {}).get("version") or "",
        "trace_sample_size": stats.get("sample_size") or 0,
        "trace_project_count": stats.get("project_count") or 0,
        "workspace_projects": Project.objects.filter(pipeline_mode=Project.MODE_WORKSPACE).count(),
        "from_reference_projects": Project.objects.filter(creation_entry="from-reference").count(),
        "top_sub_skills": top_skills,
        "execution": execution,
    }


class AdminCreationProjectListView(APIView):
    """GET /api/admin/creation/projects/ — 创作项目运营列表。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        status_filter = (request.query_params.get("status") or "").strip()
        pipeline_mode = (request.query_params.get("pipeline_mode") or "").strip()
        creation_entry = (request.query_params.get("creation_entry") or "").strip()
        keyword = (request.query_params.get("keyword") or "").strip()
        has_failed_run = (request.query_params.get("has_failed_run") or "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        try:
            page = max(1, int(request.query_params.get("page", "1")))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(50, max(1, int(request.query_params.get("page_size", "20"))))
        except (TypeError, ValueError):
            page_size = 20

        qs = Project.objects.select_related("user").order_by("-updated_at")
        if status_filter in dict(Project.STATUS_CHOICES):
            qs = qs.filter(status=status_filter)
        if pipeline_mode in dict(Project.PIPELINE_MODE_CHOICES):
            qs = qs.filter(pipeline_mode=pipeline_mode)
        if creation_entry:
            qs = qs.filter(creation_entry=creation_entry)
        if keyword:
            qs = qs.filter(
                Q(title__icontains=keyword)
                | Q(theme__icontains=keyword)
                | Q(core_idea__icontains=keyword)
                | Q(user__phone__icontains=keyword)
            )
        if has_failed_run:
            from apps.creation.models import AgentExecutionRun

            qs = qs.filter(
                id__in=AgentExecutionRun.objects.filter(
                    status=AgentExecutionRun.STATUS_FAILED
                ).values("project_id")
            )

        total = qs.count()
        start = (page - 1) * page_size
        page_qs = list(qs[start : start + page_size])
        artifact_map = _batch_artifact_map([p.id for p in page_qs])
        from apps.creation.monitoring.execution_run_service import AgentExecutionRunService

        execution_map = AgentExecutionRunService.batch_project_execution_summary(
            [p.id for p in page_qs]
        )
        items = [
            _project_ops_row(
                p,
                artifact_map.get(p.id),
                execution_map.get(str(p.id), {}),
            )
            for p in page_qs
        ]
        total_pages = (total + page_size - 1) // page_size if page_size else 0

        pagination: Dict[str, Any] = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
        facets = None
        if (request.query_params.get("facets") or "").strip().lower() in ("1", "true", "yes"):
            from apps.creation.models import AgentExecutionRun

            failed_project_ids = AgentExecutionRun.objects.filter(
                status=AgentExecutionRun.STATUS_FAILED
            ).values("project_id")
            facets = {
                "all": Project.objects.count(),
                "running": Project.objects.filter(status=Project.STATUS_RUNNING).count(),
                "failed": Project.objects.filter(status=Project.STATUS_FAILED).count(),
                "pending": Project.objects.filter(status=Project.STATUS_PENDING).count(),
                "awaiting": Project.objects.filter(status=Project.STATUS_AWAITING).count(),
                "workspace": Project.objects.filter(pipeline_mode=Project.MODE_WORKSPACE).count(),
                "has_failed_run": Project.objects.filter(id__in=failed_project_ids).count(),
            }

        response = api_ok(items)
        response.data["pagination"] = pagination
        if facets is not None:
            response.data["facets"] = facets
        return response


class AdminCreationProjectDetailView(APIView):
    """DELETE /api/admin/creation/projects/<project_id>/ — 运营删除创作项目。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, project_id: str):
        from django.core.exceptions import PermissionDenied

        try:
            data = CreationService.admin_delete_project(project_id)
        except PermissionDenied as exc:
            return api_fail(str(exc), code=403)
        except Exception as exc:  # noqa: BLE001
            return api_fail(str(exc) or "删除失败", code=500)
        return api_ok(data)
