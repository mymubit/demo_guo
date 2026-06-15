# -*- coding: utf-8 -*-
"""OutlineAgent：六阶段粗纲 + 逐集大纲 + sub-plan 校验。"""
from __future__ import annotations

import logging

from apps.common.user_messages import humanize_pipeline_error, humanize_user_message
from apps.workflow.fusion import get_artifact_registry

from ..artifact_service import get_artifact
from ..artifact_readiness import require_upstream_artifacts
from ..fusion.fusion_orchestrator import FusionOrchestrator
from ..models import Project
from ..pipeline_debug_log import log_fusion_node_fail
from .outline_engine import AGENT_ID, OutlineAgentEngine
from .sub_skill_runner import agent_execution_meta
from apps.agent.runtime import get_agent
from .types import AgentResult, WorkspaceInvokeOptions

logger = logging.getLogger(__name__)


def run_outline_agent(
    project: Project,
    *,
    options: WorkspaceInvokeOptions | None = None,
) -> AgentResult:
    """OutlineAgent 主入口（工作台 / 分步均走此路径）。"""
    opts = options or WorkspaceInvokeOptions(node_index=4)
    agent_def = get_agent(AGENT_ID) or {}
    orch = FusionOrchestrator(project)
    engine = None

    try:
        missing = require_upstream_artifacts(
            project, ("project_brief", "structure_plan", "character_bible")
        )
        if missing:
            return AgentResult(agent_id=AGENT_ID, status="error", errors=[missing])

        artifacts = orch.load_artifacts_from_db()
        engine = OutlineAgentEngine(orch)
        existing = get_artifact(project, "series_outline") or {}

        if opts.outline_mode == "framework":
            payload = engine.run_workspace(artifacts, framework_only=True, existing=existing)
        elif opts.outline_mode == "stage_framework":
            stage_key = (opts.outline_stage_key or "").strip()
            if not stage_key:
                return AgentResult(
                    agent_id=AGENT_ID,
                    status="error",
                    errors=["未指定大纲阶段"],
                )
            payload = engine.run_workspace(
                artifacts,
                stage_key=stage_key,
                existing=existing,
            )
        elif opts.outline_mode == "episodes":
            payload = engine.run_workspace(
                artifacts,
                from_episode=opts.outline_from or opts.script_from or 1,
                to_episode=opts.outline_to or opts.script_to or 1,
                existing=existing,
            )
        else:
            payload = engine.run_workspace(artifacts, existing=existing)

        orch._persist_node("node-4-outline", payload)
        artifact_key = get_artifact_registry().primary_artifact_for_fusion_node("node-4-outline")

        return AgentResult(
            agent_id=AGENT_ID,
            status="completed",
            outputs={"artifact_key": artifact_key, "series_outline": payload},
            meta=agent_execution_meta(
                AGENT_ID,
                engine.executed_skills,
                node_index=4,
                trace_entries=engine.orchestrator.state.to_trace_list(AGENT_ID),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[OutlineAgent] failed project=%s", project.id)
        msg = humanize_user_message(str(exc), default="大纲生成失败")
        log_fusion_node_fail(
            project_id=project.id,
            node_id="node-4-outline",
            node_index=4,
            error=humanize_pipeline_error(str(exc)),
            upstream=None,
        )
        orch._mark_node_failed("node-4-outline", msg[:500])
        orch._flush_progress()
        return AgentResult(
            agent_id=AGENT_ID,
            status="error",
            errors=[msg],
            meta={"node_index": 4, "executed_sub_skills": getattr(engine, "executed_skills", [])},
        )
