# -*- coding: utf-8 -*-
"""LEGACY — 工作台节点 → 子技能编排入口，独立 Agent 工作台不使用。"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ..models import Project
from .types import AgentResult
from .brief import run_brief_agent
from .character import run_character_agent
from .outline import run_outline_agent
from .script import run_script_agent
from .world import run_world_agent

AgentRunner = Callable[..., AgentResult]

WORKSPACE_AGENT_RUNNERS: Dict[str, AgentRunner] = {
    "brief": run_brief_agent,
    "world": run_world_agent,
    "character": run_character_agent,
    "outline": run_outline_agent,
    "script": run_script_agent,
}


def invoke_workspace_agent(
    project: Project,
    node_index: int,
    *,
    script_from: Optional[int] = None,
    script_to: Optional[int] = None,
    outline_mode: Optional[str] = None,
    outline_stage_key: Optional[str] = None,
) -> Any:
    """返回 SkillAgentResult（与 tasks._invoke_workspace_skill 兼容）。"""
    from apps.agent.runtime import agent_for_workspace_index

    from ..workspace_skill_invoke import (
        SkillAgentResult,
        invoke_workspace_skill_flat,
        workspace_node_to_skill_id,
    )

    agent_id = agent_for_workspace_index(node_index) or ""
    runner = WORKSPACE_AGENT_RUNNERS.get(agent_id)
    if runner:
        result = runner(
            project,
            node_index=node_index,
            script_from=script_from,
            script_to=script_to,
            outline_mode=outline_mode,
            outline_stage_key=outline_stage_key,
        )
        artifact_key = str((result.outputs or {}).get("artifact_key") or "")
        fusion_ok = result.status == "completed"
        return SkillAgentResult(
            status="completed" if fusion_ok else "error",
            agent_id=agent_id,
            outputs={**(result.outputs or {}), "artifact_key": artifact_key},
            errors=list(result.errors or []),
            meta={
                **(result.meta or {}),
                "agent_id": agent_id,
                "skill_id": workspace_node_to_skill_id(node_index),
                "fusion": {
                    "ok": fusion_ok,
                    "skipped": result.status == "skipped",
                    "status": "completed" if fusion_ok else "error",
                    "artifact_key": artifact_key,
                    "error": "; ".join(result.errors or [])[:200],
                },
                "executed_sub_skills": (result.meta or {}).get("executed_sub_skills") or [],
                "execution_trace": (result.meta or {}).get("execution_trace") or [],
            },
        )

    return invoke_workspace_skill_flat(
        project,
        node_index,
        script_from=script_from,
        script_to=script_to,
        outline_mode=outline_mode,
        outline_stage_key=outline_stage_key,
    )
