# -*- coding: utf-8 -*-
"""BriefAgent：节点 1 立项 brief 补全（reference-injector + sub-brief CLI）。"""
from __future__ import annotations

import logging
from typing import List

from ..artifact_service import save_artifact
from ..models import Project
from ..workspace.workspace_editor import _mark_skill_has_content
from .agent_common import load_project_brief
from .sub_skill_runner import (
    agent_execution_meta,
    inject_knowledge_upstream,
    mark_executed,
    persist_execution_trace,
)
from .types import AgentResult

logger = logging.getLogger(__name__)

AGENT_ID = "brief"
NODE_INDEX = 1



def run_brief_agent(project: Project, *, node_index: int = NODE_INDEX, **_kwargs) -> AgentResult:
    executed: List[str] = []
    errors: List[str] = []

    brief = load_project_brief(project)
    upstream = {
        "projectBrief": brief,
        "project_brief": brief,
        "theme": project.theme or brief.get("theme") or "",
        "episodeCount": project.episode_count or brief.get("episodeCount"),
    }

    try:
        upstream = inject_knowledge_upstream(AGENT_ID, upstream, project)
        mark_executed(executed, "reference-injector")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[BriefAgent] reference-injector skipped: %s", exc)

    try:
        from apps.creation.validators import enrich_brief, validate_brief

        brief = enrich_brief(brief, project)
        validation = validate_brief(brief)
        if not validation.passed:
            logger.warning("[BriefAgent] brief 校验警告: %s", validation.issues)
        mark_executed(executed, "brief-enricher")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[BriefAgent] brief-enricher skipped: %s", exc)
        errors.append(f"brief-enricher: {exc}")

    try:
        save_artifact(project, "project_brief", brief)
        title = (brief.get("workingTitle") or project.title or "立项").strip()
        _mark_skill_has_content(project, node_index, title[:40])
    except Exception as exc:  # noqa: BLE001
        logger.exception("[BriefAgent] finalize failed")
        errors.append(str(exc))

    persist_execution_trace(project, node_index, AGENT_ID, executed)
    status = "completed" if not errors else "error"
    return AgentResult(
        agent_id=AGENT_ID,
        status=status,
        outputs={"project_brief": brief, "artifact_key": "project_brief"},
        errors=errors,
        meta=agent_execution_meta(AGENT_ID, executed, node_index=node_index),
    )
