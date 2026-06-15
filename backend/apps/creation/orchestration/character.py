# -*- coding: utf-8 -*-
"""CharacterAgent：人物圣经 + 原型匹配 + 关系网。"""
from __future__ import annotations

import logging

from apps.common.user_messages import humanize_user_message
from apps.workflow.fusion import get_artifact_registry

from ..artifact_readiness import require_upstream_artifacts
from ..fusion.fusion_orchestrator import FusionOrchestrator
from ..models import Project
from .sub_skill_runner import agent_execution_meta
from .character_engine import AGENT_ID, CharacterAgentEngine
from apps.agent.runtime import get_agent
from .types import AgentResult, WorkspaceInvokeOptions

logger = logging.getLogger(__name__)


def run_character_agent(
    project: Project,
    *,
    options: WorkspaceInvokeOptions | None = None,
) -> AgentResult:
    agent_def = get_agent(AGENT_ID) or {}
    orch = FusionOrchestrator(project)
    engine = CharacterAgentEngine(orch)

    try:
        missing = require_upstream_artifacts(project, ("project_brief", "structure_plan"))
        if missing:
            return AgentResult(agent_id=AGENT_ID, status="error", errors=[missing])

        artifacts = orch.load_artifacts_from_db()
        payload = engine.generate(artifacts)
        orch._persist_node("node-3-character", payload)
        artifact_key = get_artifact_registry().primary_artifact_for_fusion_node("node-3-character")
        return AgentResult(
            agent_id=AGENT_ID,
            status="completed",
            outputs={"artifact_key": artifact_key, "character_bible": payload},
            meta=agent_execution_meta(
                AGENT_ID,
                engine.executed_skills,
                node_index=3,
                trace_entries=engine.orchestrator.state.to_trace_list(AGENT_ID),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[CharacterAgent] failed project=%s", project.id)
        msg = humanize_user_message(str(exc), default="人物体系生成失败")
        orch._mark_node_failed("node-3-character", msg[:500])
        return AgentResult(agent_id=AGENT_ID, status="error", errors=[msg])
