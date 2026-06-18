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
        payload = AgentExecutionRunService.get_run_detail(run_id, include_sub_skills=True)
        if not payload:
            return api_fail("执行记录不存在", code=404)
        return api_ok(payload)


# ────────────────────────────────────────────────
# 任务干预 / 节点跳转
# ────────────────────────────────────────────────

class TaskInterventionView(APIView):
    """POST /api/admin/orchestration/tasks/<task_id>/intervene/ — 人工干预任务。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, task_id: str):
        """action 可选值：retry_node / abort / force_next / adjust_pack。"""
        from apps.creation.models import CreationTask

        try:
            task = CreationTask.objects.select_related("project").get(id=task_id)
        except (CreationTask.DoesNotExist, ValueError):
            return api_fail("任务不存在", code=404)

        data = request.data or {}
        action = str(data.get("action") or "").strip()
        if action not in ("retry_node", "abort", "force_next", "adjust_pack"):
            return api_fail("action 必须为 retry_node / abort / force_next / adjust_pack")

        affected_nodes = []
        new_status = task.state

        if action == "retry_node":
            # 重新执行当前节点
            if task.state not in (CreationTask.STATE_RUNNING, CreationTask.STATE_FAILED):
                return api_fail("仅 running 或 failed 状态的任务可以重试节点")
            task.state = CreationTask.STATE_RUNNING
            task.error_code = ""
            task.error_message = ""
            task.retry_count = task.retry_count + 1
            task.save(update_fields=["state", "error_code", "error_message", "retry_count", "updated_at"])
            affected_nodes = [task.current_node_index]
            new_status = task.state

        elif action == "abort":
            # 强制终止任务
            task.state = CreationTask.STATE_FAILED
            task.error_code = "ADMIN_ABORT"
            task.error_message = "管理员强制终止"
            task.save(update_fields=["state", "error_code", "error_message", "updated_at"])
            # 同时更新关联 project 状态
            if task.project:
                task.project.status = "failed"
                task.project.save(update_fields=["status", "updated_at"])
            affected_nodes = []
            new_status = task.state

        elif action == "force_next":
            # 跳过当前节点进入下一节点（仅 step 模式）
            if task.project and task.project.pipeline_mode != "step":
                return api_fail("force_next 仅在 step 模式下可用")
            next_index = task.current_node_index + 1
            if next_index > task.project.total_nodes:
                return api_fail("已无下一节点可跳转")
            task.current_node_index = next_index
            task.progress_percent = min(100, int(next_index / task.project.total_nodes * 100))
            task.save(update_fields=["current_node_index", "progress_percent", "updated_at"])
            affected_nodes = [task.current_node_index - 1, task.current_node_index]
            new_status = task.state

        elif action == "adjust_pack":
            # 运行时切换工作流包（需确认）
            pack_id = str(data.get("pack_id") or "").strip()
            if not pack_id:
                return api_fail("adjust_pack 需要 pack_id")
            try:
                from apps.workflow.models import FusionPipelinePack
                pack = FusionPipelinePack.objects.get(pk=pack_id)
            except FusionPipelinePack.DoesNotExist:
                return api_fail("工作流包不存在")
            if task.project:
                task.project.workflow = pack
                task.project.save(update_fields=["workflow", "updated_at"])
            affected_nodes = []
            new_status = task.state

        return api_ok({
            "message": f"干预 action={action} 已完成",
            "new_status": new_status,
            "affected_nodes": affected_nodes,
        })


class TaskNodeJumpView(APIView):
    """POST /api/admin/orchestration/tasks/<task_id>/jump/ — 跳转节点。"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, task_id: str):
        """输入：{target_node_index: int}，将 project.current_node_index 设为 target（跳过中间节点）。"""
        from apps.creation.models import CreationTask

        try:
            task = CreationTask.objects.select_related("project").get(id=task_id)
        except (CreationTask.DoesNotExist, ValueError):
            return api_fail("任务不存在", code=404)

        data = request.data or {}
        try:
            target_node_index = int(data.get("target_node_index", 0))
        except (TypeError, ValueError):
            return api_fail("target_node_index 必须为整数")

        if target_node_index < 0:
            return api_fail("target_node_index 不能为负数")

        old_node_index = task.current_node_index
        total_nodes = task.project.total_nodes if task.project else 7

        if target_node_index > total_nodes:
            return api_fail(f"target_node_index 不能超过总节点数 {total_nodes}")

        # 跳过中间节点
        task.current_node_index = target_node_index
        task.progress_percent = min(100, int(target_node_index / total_nodes * 100))
        task.save(update_fields=["current_node_index", "progress_percent", "updated_at"])

        return api_ok({
            "message": f"已从节点 {old_node_index} 跳转到 {target_node_index}",
            "old_node_index": old_node_index,
            "new_node_index": target_node_index,
            "progress_percent": task.progress_percent,
        })
