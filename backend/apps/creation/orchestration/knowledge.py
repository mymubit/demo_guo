# -*- coding: utf-8 -*-
"""KnowledgeAgent：参考检索与拉片回写。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from apps.workflow.fusion.ssot_catalog import get_ssot_catalog

from ..artifact_service import get_artifact, save_artifact
from ..models import Project
from ..smart_search import run_smart_search
from ..theme_recommender import recommend_themes
from .sub_skill_runner import (
    agent_execution_meta,
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
    requested = [tag for tag in (tags or []) if isinstance(tag, str) and tag.strip()]
    files = [fname for fname in requested if fname in _REFERENCE_FILES] or list(_REFERENCE_FILES)
    max_blocks = max(1, int(limit or 1))

    for fname in files[:max_blocks]:
        raw = ReferenceLibraryService.get_json(fname)
        if not raw:
            continue
        blocks.append({"file": fname, "excerpt": _summarize_json(raw, limit=limit)})

    return {
        "theme": theme,
        "themeDisplayName": theme_name,
        "tags": tags or [],
        "blocks": blocks[:max_blocks],
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
    max_items = max(1, int(limit or 1))
    if isinstance(raw, list):
        return [_summarize_json(item, limit=max_items) for item in raw[:max_items]]
    if isinstance(raw, dict):
        keys = list(raw.keys())[:max_items]
        return {k: _summarize_json(raw[k], limit=max_items) for k in keys}
    return raw


def run_pipeline_writeback(
    project: Project,
    insight_report: Dict[str, Any],
    *,
    dry_run: bool = True,
) -> AgentResult:
    """sub-pipeline：拉片结果回写 references（默认 dry_run，待运营审核）。"""
    executed: list = []
    mark_executed(executed, "pipeline-writeback")
    payload = {
        "dryRun": dry_run,
        "ok": False,
        "disabled": True,
        "pendingReview": True,
        "reason": "external writeback runtime removed",
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
