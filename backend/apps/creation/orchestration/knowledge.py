# -*- coding: utf-8 -*-
"""KnowledgeAgent：参考检索与拉片回写。"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

from apps.workflow.fusion import FusionCliRunner, get_fusion_config
from apps.workflow.fusion.ssot_catalog import get_ssot_catalog

from ..artifact_service import get_artifact, save_artifact
from ..models import Project
from ..smart_search import run_smart_search
from ..theme_recommender import recommend_themes
from .sub_skill_runner import (
    agent_execution_meta,
    cli_pipeline_writeback,
    mark_executed,
    persist_agent_execution_trace,
)
from .types import AgentResult

logger = logging.getLogger(__name__)

_REFERENCE_FILES = (
    "hook-types-library.json",
    "reversal-patterns-library.json",
    "character-archetypes.json",
    "theme-templates.json",
    "industry-benchmarks.json",
    "douyin-formula-library.json",
)


def retrieve_references(
    *,
    theme: str = "",
    tags: Optional[List[str]] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """为生成 Agent 注入的轻量 RAG 上下文。"""
    from apps.skill.config.portal.reference_libs import ReferenceLibraryService

    blocks: List[Dict[str, Any]] = []
    catalog = get_ssot_catalog()
    theme_name = catalog.theme_display_name(theme) if theme else ""

    for fname in _REFERENCE_FILES:
        raw = ReferenceLibraryService.get_json(fname)
        if not raw:
            continue
        blocks.append({"file": fname, "excerpt": _summarize_json(raw, limit=limit)})

    return {
        "theme": theme,
        "themeDisplayName": theme_name,
        "tags": tags or [],
        "blocks": blocks[:limit],
    }


def run_knowledge_search(project: Project, *, query: str = "", limit: int = 8) -> AgentResult:
    """smart-search：基于项目 brief 检索对标剧本与题材模板。"""
    executed: list = []
    brief = get_artifact(project, "project_brief") or {}
    theme = (brief.get("theme") or getattr(project, "theme", "") or "").strip()
    q = (query or "").strip() or (brief.get("coreHook") or brief.get("coreIdea") or theme or project.title or "")

    search = run_smart_search(q, theme=theme, limit=limit)
    recs = recommend_themes(brief, limit=5, current_theme=theme)
    payload = {
        "agentId": "knowledge",
        "query": q,
        "smartSearch": search,
        "themeRecommendations": recs,
    }
    mark_executed(executed, "smart-search")
    mark_executed(executed, "theme-recommender")
    save_artifact(project, "retrieval_context", payload)
    trace_meta = agent_execution_meta("knowledge", executed, node_index=0)
    persist_agent_execution_trace(project, "knowledge", executed)
    return AgentResult(
        agent_id="knowledge",
        status="completed",
        outputs={"retrieval_context": payload},
        meta=trace_meta,
    )


def _summarize_json(raw: Any, *, limit: int) -> Any:
    if isinstance(raw, list):
        return raw[:limit]
    if isinstance(raw, dict):
        keys = list(raw.keys())[:limit]
        return {k: raw[k] for k in keys}
    return raw


def run_pipeline_writeback(
    project: Project,
    insight_report: Dict[str, Any],
    *,
    dry_run: bool = True,
) -> AgentResult:
    """sub-pipeline：拉片结果回写 references（默认 dry_run，待运营审核）。"""
    executed: list = []
    try:
        runner = FusionCliRunner(get_fusion_config())
        work = Path(getattr(settings, "CREATION_FUSION_WORK_DIR", "/tmp/scriptforge_fusion"))
        work.mkdir(parents=True, exist_ok=True)
        inp = work / f"{project.id.hex}_pipeline_analysis.json"
        inp.write_text(json.dumps(insight_report, ensure_ascii=False), encoding="utf-8")
        mark_executed(executed, "pipeline-writeback")
        cli = cli_pipeline_writeback(runner, inp, dry_run=dry_run)
        payload = cli.get("json") or {"ok": cli.get("ok"), "dryRun": dry_run}
        mark_executed(executed, "writeback-review")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[KnowledgeAgent] pipeline writeback skipped: %s", exc)
        payload = {
            "dryRun": dry_run,
            "ok": False,
            "error": str(exc),
            "pendingReview": True,
        }

    save_artifact(
        project,
        "references_updates",
        {"agentId": "knowledge", "pipelineWriteback": payload, "sourceInsight": str(project.id)},
    )
    trace_meta = agent_execution_meta("knowledge", executed, node_index=0)
    persist_agent_execution_trace(project, "knowledge", executed)
    status = "completed" if payload.get("ok") else "error"
    return AgentResult(
        agent_id="knowledge",
        status=status,
        outputs={"references_updates": payload},
        meta=trace_meta,
    )
