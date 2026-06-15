# -*- coding: utf-8 -*-
"""Agent 执行基座：registry 元数据 + FusionOrchestrator 引擎。"""
from __future__ import annotations

import logging
from typing import Dict, List

from ..models import Project
from apps.agent.runtime import agent_for_workspace_index, get_agent, resolve_agent_runner
from .types import AgentResult, WorkspaceInvokeOptions

logger = logging.getLogger(__name__)


def sub_skill_trace(agent_id: str) -> List[Dict[str, str]]:
    agent = get_agent(agent_id) or {}
    trace: List[Dict[str, str]] = []
    for skill in agent.get("sub_skills") or []:
        if not isinstance(skill, dict):
            continue
        trace.append(
            {
                "id": str(skill.get("id") or ""),
                "type": str(skill.get("type") or ""),
                "cli": str(skill.get("cli") or ""),
            }
        )
    return trace


def run_workspace_agent(project: Project, options: WorkspaceInvokeOptions) -> AgentResult:
    """按 registry 配置的 agent_id 动态解析 runner 并执行。"""
    agent_id = agent_for_workspace_index(int(options.node_index))
    if not agent_id:
        return AgentResult(
            agent_id="unknown",
            status="error",
            errors=[f"工作台节点未配置可执行 Agent: {options.node_index}"],
        )
    runner = resolve_agent_runner(agent_id)
    if not runner:
        return AgentResult(
            agent_id=agent_id,
            status="error",
            errors=[f"Agent {agent_id} 的 runner 未配置或无法加载"],
        )
    return runner(project, options=options)
