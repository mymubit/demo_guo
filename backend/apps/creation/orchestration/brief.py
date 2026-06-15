# -*- coding: utf-8 -*-
"""BriefAgent：立项策划（sub-brief / 题材匹配 / IP 锁定）。"""
from __future__ import annotations

import logging

from apps.common.user_messages import humanize_user_message
from apps.workflow.fusion import get_artifact_registry

from ..fusion.fusion_orchestrator import FusionOrchestrator
from ..models import Project
from .brief_engine import AGENT_ID, BriefAgentEngine
from .sub_skill_runner import agent_execution_meta
from apps.agent.runtime import get_agent
from .types import AgentResult, WorkspaceInvokeOptions

logger = logging.getLogger(__name__)


def run_brief_agent(project: Project, *, options: WorkspaceInvokeOptions | None = None) -> AgentResult:
    agent_def = get_agent(AGENT_ID) or {}
    orch = FusionOrchestrator(project)
    engine = BriefAgentEngine(orch)

    try:
        artifacts = orch.load_artifacts_from_db()
        payload = engine.generate(artifacts)
        orch._persist_node("node-1-input", payload)
        artifact_key = get_artifact_registry().primary_artifact_for_fusion_node("node-1-input")
        return AgentResult(
            agent_id=AGENT_ID,
            status="completed",
            outputs={"artifact_key": artifact_key, "project_brief": payload},
            meta=agent_execution_meta(
                AGENT_ID,
                engine.executed_skills,
                node_index=1,
                trace_entries=engine.orchestrator.state.to_trace_list(AGENT_ID),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[BriefAgent] failed project=%s", project.id)
        msg = humanize_user_message(str(exc), default="立项整理失败")
        orch._mark_node_failed("node-1-input", msg[:500])
        return AgentResult(agent_id=AGENT_ID, status="error", errors=[msg])
