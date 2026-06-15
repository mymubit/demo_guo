# -*- coding: utf-8 -*-
"""WorldAgent：六阶段结构 + 世界观 + sub-world 校验。"""
from __future__ import annotations

import logging

from apps.common.user_messages import humanize_user_message
from apps.workflow.fusion import get_artifact_registry

from ..artifact_readiness import require_upstream_artifacts
from ..fusion.fusion_orchestrator import FusionOrchestrator
from ..models import Project
from .sub_skill_runner import agent_execution_meta
from apps.agent.runtime import get_agent
from .types import AgentResult, WorkspaceInvokeOptions
from .world_engine import AGENT_ID, WorldAgentEngine

logger = logging.getLogger(__name__)


def run_world_agent(project: Project, *, options: WorkspaceInvokeOptions | None = None) -> AgentResult:
    agent_def = get_agent(AGENT_ID) or {}
    orch = FusionOrchestrator(project)
    engine = WorldAgentEngine(orch)

    try:
        missing = require_upstream_artifacts(project, ("project_brief",))
        if missing:
            return AgentResult(agent_id=AGENT_ID, status="error", errors=[missing])

        artifacts = orch.load_artifacts_from_db()
        payload = engine.generate(artifacts)
        orch._persist_node("node-2-structure", payload)
        artifact_key = get_artifact_registry().primary_artifact_for_fusion_node("node-2-structure")
        return AgentResult(
            agent_id=AGENT_ID,
            status="completed",
            outputs={"artifact_key": artifact_key, "structure_plan": payload},
            meta=agent_execution_meta(
                AGENT_ID,
                engine.executed_skills,
                node_index=2,
                trace_entries=engine.orchestrator.state.to_trace_list(AGENT_ID),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[WorldAgent] failed project=%s", project.id)
        msg = humanize_user_message(str(exc), default="结构与世界观生成失败")
        orch._mark_node_failed("node-2-structure", msg[:500])
        return AgentResult(agent_id=AGENT_ID, status="error", errors=[msg])
