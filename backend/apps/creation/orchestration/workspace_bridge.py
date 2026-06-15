# -*- coding: utf-8 -*-
"""工作台五步 → 各 Workspace Agent（不再直连 FusionOrchestrator）。"""
from __future__ import annotations

import logging

from ..models import Project
from .base import run_workspace_agent
from apps.agent.runtime import agent_for_workspace_index
from .types import AgentResult, WorkspaceInvokeOptions

logger = logging.getLogger(__name__)


def run_workspace_node(project: Project, options: WorkspaceInvokeOptions) -> AgentResult:
    agent_id = agent_for_workspace_index(options.node_index) or "unknown"
    logger.info(
        "[WorkspaceBridge] agent=%s node=%s project=%s",
        agent_id,
        options.node_index,
        project.id,
    )
    return run_workspace_agent(project, options)
