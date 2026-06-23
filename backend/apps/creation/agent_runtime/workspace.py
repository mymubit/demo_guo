# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.artifact_service import get_artifact
from apps.creation.models import AgentExecutionRun, Project, ProjectFusionArtifact
from apps.creation.agent_runtime.entry_plan import filter_agents_for_workspace, get_entry_plan
from apps.creation.monitoring.execution_run_service import AgentExecutionRunService


def _missing_inputs(project: Project, contract: Dict[str, Any]) -> List[str]:
    missing = []
    for key in contract.get("required_artifacts") or []:
        payload = get_artifact(project, str(key))
        if payload in (None, {}, []):
            missing.append(str(key))
    return missing


def build_independent_workspace(project: Project) -> Dict[str, Any]:
    AgentDefinitionService.ensure_defaults()
    artifacts = list(ProjectFusionArtifact.objects.filter(project=project).order_by("artifact_key"))
    artifact_keys = {row.artifact_key for row in artifacts}
    latest_runs = AgentExecutionRunService.latest_runs_by_agent(project)
    agent_items = []
    for agent in AgentDefinitionService.active_agents():
        contract = agent.input_contract or {}
        output_contract = agent.output_contract or {}
        outputs = [str(k) for k in output_contract.get("artifacts") or []]
        missing = _missing_inputs(project, contract)
        latest = latest_runs.get(agent.agent_id)
        health = AgentDefinitionService.health(agent)
        policy = agent.runtime_policy or {}
        from apps.creation.agent_runtime.agent_billing import billing_preview

        billing = billing_preview(agent.agent_id)
        agent_items.append(
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "name_zh": agent.name_zh,
                "description": agent.description,
                "enabled": agent.is_enabled,
                "required_inputs": [str(k) for k in contract.get("required_artifacts") or []],
                "missing_inputs": missing,
                "output_artifacts": outputs,
                "has_output": any(key in artifact_keys for key in outputs),
                "can_run": not missing and health.get("healthy", False),
                "latest_run": latest,
                "coin_cost": billing["coin_cost"],
                "action_key": billing["action_key"],
                "token_policy": {
                    "max_prompt_tokens": policy.get("max_prompt_tokens"),
                    "max_completion_tokens": policy.get("max_completion_tokens"),
                },
                "health": health,
                "ui_schema": agent.ui_schema or {},
                "workspace_order": agent.workspace_order,
            }
        )
    agent_items = filter_agents_for_workspace(agent_items, getattr(project, "creation_entry", "") or "from-scratch")
    entry_plan = get_entry_plan(getattr(project, "creation_entry", "") or "from-scratch")
    can_download = "episode_scripts" in artifact_keys
    from apps.drama.progress_service import DramaProgressService

    can_share = DramaProgressService.is_deliverable(project) and can_download
    has_running_agent = AgentExecutionRun.objects.filter(
        project=project,
        status=AgentExecutionRun.STATUS_RUNNING,
    ).exists()
    return {
        "project": {
            "id": str(project.id),
            "title": project.title or project.theme,
            "status": project.execution_status,
            "episode_count": project.episode_count,
            "can_download": can_download,
            "can_share": can_share,
            "has_running_agent": has_running_agent,
        },
        "agents": agent_items,
        "entry_plan": entry_plan,
        "agent_notes": dict(getattr(project, "agent_notes", None) or {}),
        "artifacts": [
            {
                "artifact_key": row.artifact_key,
                "exists": True,
                "updated_at": row.updated_at.isoformat() if row.updated_at else "",
                "version": row.version,
            }
            for row in artifacts
        ],
    }


def build_workspace_catalog() -> Dict[str, Any]:
    """C 端创作页展示用：独立 Agent 能力目录（与真实工作台一致）。"""
    AgentDefinitionService.ensure_defaults()
    items = []
    for agent in AgentDefinitionService.active_agents():
        contract = agent.input_contract or {}
        output_contract = agent.output_contract or {}
        policy = agent.runtime_policy or {}
        from apps.creation.agent_runtime.agent_billing import billing_preview

        billing = billing_preview(agent.agent_id)
        items.append(
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "name_zh": agent.name_zh,
                "description": agent.description,
                "workspace_order": agent.workspace_order,
                "required_inputs": [str(k) for k in contract.get("required_artifacts") or []],
                "output_artifacts": [str(k) for k in output_contract.get("artifacts") or []],
                "coin_cost": billing["coin_cost"],
                "action_key": billing["action_key"],
                "token_policy": {
                    "max_prompt_tokens": policy.get("max_prompt_tokens"),
                    "max_completion_tokens": policy.get("max_completion_tokens"),
                },
            }
        )
    return {
        "agents": items,
        "mode": "independent",
        "hint": "提交后进入工作台，由你手动逐个运行 Agent，不会自动执行主链流水线。",
    }
