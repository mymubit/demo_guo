# -*- coding: utf-8 -*-
"""Admin Agent 执行记录与项目轨迹 API。"""
from __future__ import annotations

from typing import Any, Dict

from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import IsAdminUser
from apps.creation.admin_status import resolve_admin_status
from apps.creation.artifact_service import get_artifact, list_artifact_keys
from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
from apps.creation.models import Project, ProjectFusionArtifact, ScriptQualityDefect
from apps.creation.workspace.verify_summary import verify_summary

from apps.console.base_views import AdminAPIView
from apps.console.responses import api_fail, api_ok


def _artifact_preview(artifact_key: str, payload: dict) -> dict:
    """运营可读产物摘要（非原始 JSON 全量）。"""
    if not isinstance(payload, dict):
        return {"artifact_key": artifact_key, "preview": str(payload)[:200]}
    if artifact_key == "project_brief":
        return {
            "artifact_key": artifact_key,
            "working_title": payload.get("workingTitle") or payload.get("working_title"),
            "theme": payload.get("theme"),
            "episode_count": payload.get("episodeCount") or payload.get("episode_count"),
        }
    if artifact_key == "episode_scripts":
        episodes = payload.get("episodes") or []
        return {
            "artifact_key": artifact_key,
            "episode_count": len(episodes),
            "sample_titles": [
                ep.get("title") or f"第{ep.get('episodeNumber') or ep.get('episode_number')}集"
                for ep in episodes[:5]
            ],
        }
    if artifact_key in {"series_outline", "character_bible"}:
        return {
            "artifact_key": artifact_key,
            "top_keys": list(payload.keys())[:8],
            "episode_or_char_count": payload.get("totalEpisodes")
            or payload.get("total_episodes")
            or payload.get("characterCount")
            or payload.get("character_count"),
        }
    keys = list(payload.keys())[:10]
    return {"artifact_key": artifact_key, "top_keys": keys}


def _list_project_artifacts(project: Project) -> list:
    rows = ProjectFusionArtifact.objects.filter(project=project).order_by("artifact_key")
    return [
        _artifact_preview(row.artifact_key, row.payload if isinstance(row.payload, dict) else {})
        for row in rows
    ]


def _list_quality_defects(project: Project) -> list:
    return [
        {
            "id": row.pk,
            "episode": row.episode,
            "dimension": row.dimension,
            "defect_type": row.defect_type,
            "score": row.score,
            "details": row.details,
            "status": row.status,
            "status_label": row.get_status_display(),
            "created_at": row.created_at.isoformat() if row.created_at else "",
        }
        for row in ScriptQualityDefect.objects.filter(project=project).order_by("-created_at")[:100]
    ]


class AgentCatalogAdminView(AdminAPIView):
    """GET /api/admin/agent/catalog/ — drama.* 角色目录（Admin 轨迹/展示 SSOT）。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from apps.agent.catalog import portal_agent_catalog
        from apps.drama.services import DramaRoleService

        expert_agents = portal_agent_catalog(track_mode="expert")
        fast_agents = portal_agent_catalog(track_mode="fast")
        departments = DramaRoleService.get_all_roles_grouped()

        workspace_agents = [
            {
                "id": agent["id"],
                "name": agent.get("name"),
                "name_zh": agent.get("name_zh"),
                "workspace_index": agent.get("workspace_order"),
                "dept": agent.get("dept"),
                "is_fast_track": agent.get("is_fast_track"),
                "description": agent.get("description"),
            }
            for agent in expert_agents
        ]

        return api_ok(
            {
                "catalog_version": "drama_skills_v1",
                "agents": expert_agents,
                "workspaceAgents": workspace_agents,
                "fastTrackAgents": fast_agents,
                "departments": departments,
            }
        )


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
        execution_traces = get_artifact(project, "agent_execution_traces") or {}
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
        status, status_text = resolve_admin_status(project)
        drama_trace = None
        try:
            from apps.drama.progress_service import DramaProgressService

            if project.is_drama_workspace:
                drama_trace = DramaProgressService.build_trace_payload(project)
        except Exception:  # noqa: BLE001
            drama_trace = None
        return api_ok(
            {
                "project_id": str(project.id),
                "title": project.title,
                "theme": project.theme,
                "status": status,
                "status_text": status_text,
                "pipeline_mode": project.pipeline_mode,
                "creation_entry": project.creation_entry,
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
                "execution_traces": execution_traces if isinstance(execution_traces, dict) else {},
                "verify_summary": verify_summary(adaptation) if adaptation else None,
                "execution_runs": execution_runs,
                "latest_execution_runs": latest_by_agent,
                "artifact_keys": list_artifact_keys(project),
                "artifacts": _list_project_artifacts(project),
                "quality_defects": _list_quality_defects(project),
                "drama_trace": drama_trace,
            }
        )
