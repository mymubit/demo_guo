# -*- coding: utf-8 -*-
"""后台：创作项目运营列表与 Agent 观测摘要。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.creation.admin_status import resolve_admin_status
from apps.creation.artifact_service import get_artifact
from apps.creation.models import Project, ProjectFusionArtifact
from apps.creation.services import CreationService
from apps.creation.workspace.verify_summary import verify_summary

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
    verify = verify_summary(adaptation) if adaptation else {"hasReports": False, "allPassed": True, "stages": []}
    user = project.user
    exec_summary = execution_summary or {}
    status, status_text = resolve_admin_status(project)
    drama_summary = None
    try:
        from apps.drama.progress_service import DramaProjectProgressService

        drama = DramaProjectProgressService.find_drama_project(project.id)
        if drama:
            drama_summary = DramaProjectProgressService.build_admin_summary(drama)
            if drama.get_completion_rate() is not None:
                exec_summary = {**exec_summary, "drama_completion_rate": drama.get_completion_rate()}
    except Exception:  # noqa: BLE001
        drama_summary = None
    row = {
        "project_id": str(project.id),
        "title": (project.title or project.theme or "未命名")[:200],
        "theme": project.theme,
        "status": status,
        "status_text": status_text,
        "pipeline_mode": project.pipeline_mode,
        "creation_entry": project.creation_entry or "from-scratch",
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
        # 【运营 M2】内容质量字段
        "user_edit_count": getattr(project, "user_edit_count", 0) or 0,
        "final_export_count": getattr(project, "final_export_count", 0) or 0,
        "last_edited_at": project.last_edited_at.isoformat() if getattr(project, "last_edited_at", None) else "",
        "abandoned_at": project.abandoned_at.isoformat() if getattr(project, "abandoned_at", None) else "",
        "is_quality_sampled": getattr(project, "is_quality_sampled", False) or False,
        "drama": drama_summary,
    }
    return row


def build_creation_ops_alerts() -> Dict[str, int]:
    """Dashboard / 创作中心待办计数（Drama SSOT）。"""
    from apps.drama.models import DramaRoleExecution
    from apps.drama.progress_service import DramaProjectProgressService

    facets = DramaProjectProgressService.build_admin_facets()
    feedback_open = 0
    try:
        from apps.operations.services import feedback_summary

        feedback_open = int(feedback_summary(days=30).get("open") or 0)
    except Exception:  # noqa: BLE001
        feedback_open = 0
    alert_open = 0
    try:
        from apps.operations.models import AlertEvent

        alert_open = AlertEvent.objects.filter(status=AlertEvent.Status.OPEN).count()
    except Exception:  # noqa: BLE001
        alert_open = 0
    return {
        **facets,
        "drama_running": DramaRoleExecution.objects.filter(
            status=DramaRoleExecution.Status.RUNNING
        ).count(),
        "feedback_open": feedback_open,
        "alert_open": alert_open,
    }


def build_agent_ops_dashboard(*, stats_limit: int = 200) -> Dict[str, Any]:
    """Dashboard Agent 运营摘要。"""
    from apps.agent.runtime import get_agent_registry
    from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
    from apps.drama.models import DramaProject
    from apps.drama.progress_service import DramaProjectProgressService

    registry = get_agent_registry()
    execution = AgentExecutionRunService.dashboard_payload(days=30)
    drama = DramaProjectProgressService.dashboard_payload(days=30)
    execution["drama"] = drama

    # Drama 角色轨优先作为 Dashboard Agent 统计源
    drama_by_role = drama.get("by_role") or []
    if drama_by_role:
        execution["agent_stats"] = [
            {
                "agent_id": row["agent_id"],
                "run_count": row["run_count"],
                "failed_count": row["failed_count"],
                "failure_rate": row.get("failure_rate", 0),
                "avg_duration_ms": row.get("avg_duration_ms", 0),
            }
            for row in drama_by_role
        ]
    if drama.get("runs_7d"):
        execution["runs_7d"] = drama["runs_7d"]

    drama_today = (drama.get("summary") or {}).get("today") or {}
    if drama_today.get("run_count"):
        execution.setdefault("summary", {})
        execution["summary"]["today"] = {
            **(execution.get("summary") or {}).get("today", {}),
            **drama_today,
            "source": "drama",
        }

    return {
        "registry_version": (registry.get("_meta") or {}).get("version") or "drama_skills",
        "workspace_projects": DramaProject.objects.count(),
        "drama_projects": drama.get("drama_project_count", 0),
        "drama_running_projects": drama.get("active_project_count", 0),
        "from_reference_projects": Project.objects.filter(creation_entry="from-reference").count(),
        "execution": execution,
    }


class AdminCreationProjectListView(APIView):
    """GET /api/admin/creation/projects/ — 创作项目运营列表。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        status_filter = (request.query_params.get("status") or "").strip()
        track_mode = (request.query_params.get("track_mode") or "").strip()
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
        from apps.drama.progress_service import DramaProjectProgressService

        qs = DramaProjectProgressService.filter_creation_projects(
            qs,
            status_filter=status_filter,
            track_mode=track_mode,
            has_failed_run=has_failed_run,
        )
        if creation_entry:
            qs = qs.filter(creation_entry=creation_entry)
        if keyword:
            qs = qs.filter(
                Q(title__icontains=keyword)
                | Q(theme__icontains=keyword)
                | Q(core_idea__icontains=keyword)
                | Q(user__phone__icontains=keyword)
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
            facets = DramaProjectProgressService.build_admin_facets()

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
