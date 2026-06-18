"""
创作后台任务（Django 6 @task + dj_queue / Postgres）

主链路：run_independent_agent — 独立 Agent 工作台异步执行。
"""
from __future__ import annotations

import logging

from django.tasks import task

logger = logging.getLogger(__name__)


@task(queue_name="creation")
def run_independent_agent(
    project_id: str,
    agent_id: str,
    params: dict | None = None,
    run_id: str = "",
) -> dict:
    """执行单个独立 Agent（无 WorkflowEngine / 子技能编排）。"""
    from .agent_runtime.independent_service import IndependentAgentService
    from .models import AgentExecutionRun, Project

    run = None
    if run_id:
        run = AgentExecutionRun.objects.select_related("project").filter(id=run_id).first()
    if run is None:
        project = Project.objects.get(id=project_id)
        result = IndependentAgentService.enqueue_run(project, project.user, agent_id, params or {})
        run = result.run
    IndependentAgentService.execute_run(run)
    run.refresh_from_db()
    return {
        "run_id": str(run.id),
        "project_id": str(run.project_id),
        "agent_id": run.agent_id,
        "status": run.status,
    }
