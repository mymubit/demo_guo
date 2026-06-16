# -*- coding: utf-8 -*-
"""后台：Agent 体系目录与项目执行轨迹。"""
from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.creation.artifact_service import get_artifact, list_artifact_keys
from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
from apps.creation.models import Project, ProjectFusionArtifact
from apps.creation.workspace.workspace_service import _verify_summary, reconcile_workspace_brief_status

from apps.console.base_views import AdminAPIView
from apps.console.responses import api_fail, api_ok


def aggregate_sub_skill_stats(*, limit: int = 300) -> Dict[str, Any]:
    """聚合近期项目的 sub-skill executed/skipped 命中率。"""
    from apps.agent.runtime import get_agent_registry

    rows = list(
        ProjectFusionArtifact.objects.select_related("project")
        .filter(artifact_key="agent_execution_traces")
        .order_by("-updated_at")[:limit]
    )
    registry = get_agent_registry()
    agent_names: Dict[str, str] = {}
    skill_defs: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for agent in registry.get("agents") or []:
        if not isinstance(agent, dict):
            continue
        aid = str(agent.get("id") or "")
        agent_names[aid] = str(agent.get("name_zh") or agent.get("name") or aid)
        for skill in agent.get("sub_skills") or []:
            if isinstance(skill, dict):
                sid = str(skill.get("id") or "")
                if sid:
                    skill_defs[(aid, sid)] = skill

    buckets: Dict[Tuple[str, str], Dict[str, Any]] = {}
    seen_projects: Set[Any] = set()

    for row in rows:
        seen_projects.add(row.project_id)
        payload = row.payload if isinstance(row.payload, dict) else {}
        for agent_key, entry in payload.items():
            if not isinstance(entry, dict):
                continue
            agent_id = str(entry.get("agent_id") or "").strip()
            if not agent_id:
                try:
                    from apps.agent.runtime import agent_for_workspace_index

                    agent_id = agent_for_workspace_index(int(agent_key)) or str(agent_key)
                except (TypeError, ValueError):
                    agent_id = str(agent_key)
            trace = entry.get("execution_trace") or []
            for step in trace:
                if not isinstance(step, dict):
                    continue
                skill_id = str(step.get("id") or "")
                if not skill_id:
                    continue
                key = (agent_id, skill_id)
                if key not in buckets:
                    buckets[key] = {
                        "agent_id": agent_id,
                        "agent_name": agent_names.get(agent_id, agent_id),
                        "skill_id": skill_id,
                        "skill_type": "",
                        "executed": 0,
                        "skipped": 0,
                        "failed": 0,
                        "projects": set(),
                    }
                bucket = buckets[key]
                if not bucket["skill_type"]:
                    bucket["skill_type"] = str(
                        skill_defs.get(key, {}).get("type") or step.get("type") or ""
                    )
                status = str(step.get("status") or "")
                if status == "executed":
                    bucket["executed"] += 1
                elif status == "failed":
                    bucket.setdefault("failed", 0)
                    bucket["failed"] += 1
                elif status == "skipped":
                    bucket["skipped"] += 1
                bucket["projects"].add(row.project_id)

    from apps.creation.models import SubSkillExecutionLog

    db_rows = SubSkillExecutionLog.objects.select_related("run").order_by("-started_at")[
        : limit * 20
    ]

    for log in db_rows:
        agent_id = log.run.agent_id
        skill_id = log.skill_id
        key = (agent_id, skill_id)
        if key not in buckets:
            buckets[key] = {
                "agent_id": agent_id,
                "agent_name": agent_names.get(agent_id, agent_id),
                "skill_id": skill_id,
                "skill_type": log.skill_type or "",
                "executed": 0,
                "skipped": 0,
                "failed": 0,
                "projects": set(),
            }
        bucket = buckets[key]
        if not bucket["skill_type"]:
            bucket["skill_type"] = log.skill_type or str(
                skill_defs.get(key, {}).get("type") or ""
            )
        if log.status == SubSkillExecutionLog.STATUS_EXECUTED:
            bucket["executed"] += 1
        elif log.status == SubSkillExecutionLog.STATUS_FAILED:
            bucket["failed"] = bucket.get("failed", 0) + 1
        elif log.status == SubSkillExecutionLog.STATUS_SKIPPED:
            bucket["skipped"] += 1
        bucket["projects"].add(log.run.project_id)
        seen_projects.add(log.run.project_id)

    items: List[Dict[str, Any]] = []
    for bucket in buckets.values():
        total = bucket["executed"] + bucket["skipped"] + bucket.get("failed", 0)
        items.append(
            {
                "agent_id": bucket["agent_id"],
                "agent_name": bucket["agent_name"],
                "skill_id": bucket["skill_id"],
                "skill_type": bucket["skill_type"],
                "executed": bucket["executed"],
                "skipped": bucket["skipped"],
                "failed": bucket.get("failed", 0),
                "hit_rate": round(bucket["executed"] / total, 4) if total else 0.0,
                "project_count": len(bucket["projects"]),
            }
        )
    items.sort(key=lambda item: (-item["executed"], item["skill_id"]))

    return {
        "sample_size": len(rows),
        "project_count": len(seen_projects),
        "skills": items,
    }


class AgentCatalogAdminView(AdminAPIView):
    """GET /api/admin/agent/catalog/ — registry v2 SSOT。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        from apps.agent.catalog import portal_agent_catalog

        return api_ok(
            portal_agent_catalog(),
            request=request,
            deprecated_path="/api/admin/agent/catalog/",
        )


class AgentProjectTraceView(AdminAPIView):
    """GET /api/admin/orchestration/projects/<project_id>/traces/ — 项目级 sub-skill 轨迹。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, project_id: str):
        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return api_fail("项目不存在", code=404)

        traces = get_artifact(project, "agent_execution_traces") or {}
        adaptation = get_artifact(project, "adaptation_meta") or {}
        if reconcile_workspace_brief_status(project):
            project.refresh_from_db()
        nodes = []
        for n in project.nodes.all().order_by("node_index"):
            nodes.append(
                {
                    "node_index": n.node_index,
                    "fusion_node_id": n.fusion_node_id,
                    "name": n.node_name,
                    "status": n.status,
                    "summary": (n.summary_text or "")[:200],
                }
            )

        user = project.user
        execution_runs = AgentExecutionRunService.list_runs_for_project(project, limit=40)
        exec_summary = AgentExecutionRunService.batch_project_execution_summary([project.id]).get(
            str(project.id), {}
        )
        latest_by_agent: Dict[str, Any] = {}
        for run in execution_runs:
            agent_key = str(run.get("agent_id") or "")
            if run.get("node_index") is not None:
                agent_key = str(run.get("node_index"))
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
                "verify_summary": _verify_summary(adaptation) if adaptation else None,
                "execution_traces": traces,
                "execution_runs": execution_runs,
                "latest_execution_runs": latest_by_agent,
                "artifact_keys": list_artifact_keys(project),
                "nodes": nodes,
            }
        )


class AgentSubSkillStatsView(AdminAPIView):
    """GET /api/admin/orchestration/stats/ — 近期 sub-skill 执行命中率。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 300))
        except (TypeError, ValueError):
            limit = 300
        limit = max(1, min(limit, 1000))
        return api_ok(
            aggregate_sub_skill_stats(limit=limit),
            request=request,
            deprecated_path="/api/admin/orchestration/stats/",
        )


class OrchestrationRecentRunsView(AdminAPIView):
    """GET /api/admin/orchestration/recent-runs/ — 全站近期执行与节点态。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 40))
        except (TypeError, ValueError):
            limit = 40
        return api_ok(AgentExecutionRunService.list_recent_runs_global(limit=limit))


class AgentExecutionRunDetailView(AdminAPIView):
    """GET /api/admin/orchestration/execution-runs/<run_id>/ — 单次执行详情 + LLM 用量。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, run_id: str):
        payload = AgentExecutionRunService.get_run_detail(run_id)
        if not payload:
            return api_fail("执行记录不存在", code=404)
        return api_ok(payload)
