# -*- coding: utf-8 -*-
"""BriefAgent：节点 1 立项 brief 补全（reference-injector + sub-brief CLI）。"""
from __future__ import annotations

import logging
from typing import List

from ..artifact_service import save_artifact
from ..models import Project
from ..workspace.workspace_editor import _mark_skill_has_content
from .agent_common import deep_merge, fusion_work_dir, load_project_brief, write_json_artifact
from .sub_skill_runner import (
    agent_execution_meta,
    cli_brief_enrich,
    inject_knowledge_upstream,
    mark_executed,
    persist_execution_trace,
    unwrap_fusion_cli_result,
)
from .types import AgentResult

logger = logging.getLogger(__name__)

AGENT_ID = "brief"
NODE_INDEX = 1


def _merge_brief_cli(brief: dict, cli_payload: dict) -> dict:
    out = dict(brief)
    inner = cli_payload.get("projectBrief") if isinstance(cli_payload.get("projectBrief"), dict) else cli_payload
    if isinstance(inner, dict):
        out = deep_merge(out, inner)
    for key in ("trendFormula", "writingBrief", "targetAudience", "formatVariant", "coreHook"):
        if cli_payload.get(key) is not None:
            out[key] = cli_payload[key]
    out["agentEnriched"] = True
    out.setdefault("seedEnriched", True)
    return out


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
        mark_executed(executed, "brief-theme-matcher")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[BriefAgent] reference-injector skipped: %s", exc)

    mark_executed(executed, "brief-form-collector")

    try:
        from apps.workflow.fusion import FusionCliRunner, get_fusion_config

        input_path = fusion_work_dir(project) / "project-brief.enrich.json"
        write_json_artifact(input_path, brief)
        runner = FusionCliRunner(get_fusion_config())
        cli_raw = cli_brief_enrich(runner, input_path, strict=False)
        cli_payload = unwrap_fusion_cli_result(cli_raw)
        brief = _merge_brief_cli(brief, cli_payload)
        mark_executed(executed, "brief-enricher")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[BriefAgent] brief-enricher skipped: %s", exc)
        errors.append(f"brief-enricher: {exc}")

    mark_executed(executed, "brief-ip-lock")
    mark_executed(executed, "brief-novel-ingest")

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
