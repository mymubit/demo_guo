# -*- coding: utf-8 -*-
"""ScriptAgent：逐集剧本 + 逐集 gate + 改编约束。"""
from __future__ import annotations

import logging

from apps.common.user_messages import humanize_pipeline_error, humanize_user_message
from apps.workflow.fusion import get_artifact_registry

from ..artifact_service import get_artifact
from ..artifact_readiness import require_upstream_artifacts
from ..fusion.fusion_orchestrator import FusionOrchestrator
from ..models import Project
from ..pipeline_debug_log import log_fusion_node_fail
from .sub_skill_runner import agent_execution_meta
from apps.agent.runtime import get_agent
from .script_engine import AGENT_ID, ScriptAgentEngine
from .types import AgentResult, WorkspaceInvokeOptions

logger = logging.getLogger(__name__)


def run_script_agent(
    project: Project,
    *,
    options: WorkspaceInvokeOptions | None = None,
) -> AgentResult:
    opts = options or WorkspaceInvokeOptions(node_index=5)
    agent_def = get_agent(AGENT_ID) or {}
    orch = FusionOrchestrator(project)
    engine = None

    try:
        missing = require_upstream_artifacts(
            project,
            ("project_brief", "structure_plan", "character_bible", "series_outline"),
        )
        if missing:
            return AgentResult(agent_id=AGENT_ID, status="error", errors=[missing])

        artifacts = orch.load_artifacts_from_db()
        engine = ScriptAgentEngine(orch)
        existing = get_artifact(project, "episode_scripts") or {}

        if opts.script_from is not None and opts.script_to is not None:
            payload = engine.run_workspace(
                artifacts,
                from_episode=opts.script_from,
                to_episode=opts.script_to,
                existing=existing,
            )
        else:
            payload = engine.run_workspace(artifacts, existing=existing)

        orch._persist_node("node-5-script", payload)
        artifact_key = get_artifact_registry().primary_artifact_for_fusion_node("node-5-script")
        return AgentResult(
            agent_id=AGENT_ID,
            status="completed",
            outputs={"artifact_key": artifact_key, "episode_scripts": payload},
            meta=agent_execution_meta(
                AGENT_ID,
                engine.executed_skills,
                node_index=5,
                trace_entries=engine.orchestrator.state.to_trace_list(AGENT_ID),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[ScriptAgent] failed project=%s", project.id)
        msg = humanize_user_message(str(exc), default="剧本生成失败")
        log_fusion_node_fail(
            project_id=project.id,
            node_id="node-5-script",
            node_index=5,
            error=humanize_pipeline_error(str(exc)),
            upstream=None,
        )
        orch._mark_node_failed("node-5-script", msg[:500])
        orch._flush_progress()
        return AgentResult(
            agent_id=AGENT_ID,
            status="error",
            errors=[msg],
            meta={"node_index": 5, "executed_sub_skills": getattr(engine, "executed_skills", [])},
        )
