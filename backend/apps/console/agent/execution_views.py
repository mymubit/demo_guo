# -*- coding: utf-8 -*-
"""Admin Agent 执行记录与项目轨迹 API。"""
from __future__ import annotations

from typing import Any, Dict

from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import IsAdminUser
from apps.creation.artifact_service import get_artifact, list_artifact_keys
from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
from apps.creation.models import Project
from apps.creation.workspace.verify_summary import verify_summary

from apps.console.base_views import AdminAPIView
from apps.console.responses import api_fail, api_ok


class AgentCatalogAdminView(AdminAPIView):
    """GET /api/admin/agent/catalog/ — registry v2 SSOT。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from apps.agent.catalog import portal_agent_catalog

        return api_ok(portal_agent_catalog())


class AgentExecutionRunDetailView(AdminAPIView):
    """GET /api/admin/agent/runs/<run_id>/ — 单次执行详情。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, run_id: str):
        payload = AgentExecutionRunService.get_run_detail(run_id, include_sub_skills=False)
        if not payload:
            return api_fail("执行记录不存在", code=404)
        return api_ok(payload)


class AgentProjectTraceView(AdminAPIView):
    """GET /api/admin/agent/projects/<project_id>/traces/ — 项目级 Agent 执行轨迹。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, project_id: str):
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return api_fail("项目不存在", code=404)

        adaptation = get_artifact(project, "adaptation_meta") or {}
        user = project.user
        execution_runs = AgentExecutionRunService.list_runs_for_project(project, limit=40)
        exec_summary = AgentExecutionRunService.batch_project_execution_summary([project.id]).get(
            str(project.id), {}
        )
        latest_by_agent: Dict[str, Any] = {}
        for run in execution_runs:
            agent_key = str(run.get("agent_id") or "")
            if agent_key not in latest_by_agent:
                latest_by_agent[agent_key] = run
        return api_ok(
            {
                "project_id": str(project.id),
                "title": project.title,
                "theme": project.theme,
                "status": project.status,
                "status_text": project.get_status_display(),
                "pipeline_mode": project.pipeline_mode,
                "creation_entry": project.creation_entry,
                "fusion_status": project.fusion_status,
                "overall_score": project.overall_score,
                "grade": project.grade,
                "episode_count": project.episode_count,
                "progress_percent": project.progress_percent,
                "user_phone": getattr(user, "phone", "") or "",
                "user_id": str(user.id) if user else "",
                "created_at": project.created_at.isoformat() if project.created_at else "",
                "updated_at": project.updated_at.isoformat() if project.updated_at else "",
                "execution_run_count": exec_summary.get("run_count", 0),
                "execution_failed_count": exec_summary.get("failed_count", 0),
                "latest_failed_run": exec_summary.get("latest_failed_run"),
                "adaptation_meta": adaptation,
                "verify_summary": verify_summary(adaptation) if adaptation else None,
                "execution_runs": execution_runs,
                "latest_execution_runs": latest_by_agent,
                "artifact_keys": list_artifact_keys(project),
            }
        )
