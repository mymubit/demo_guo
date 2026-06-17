# -*- coding: utf-8 -*-
"""upstream 上下文：Prompt 裁剪与轨迹摘要（避免全量 artifact 重复塞入）。"""
from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

# camelCase / snake_case 成对字段，Prompt 侧只保留 camelCase
_ALIAS_GROUPS: Tuple[Tuple[str, str], ...] = (
    ("projectBrief", "project_brief"),
    ("structurePlan", "structure_plan"),
    ("characterBible", "character_bible"),
    ("seriesOutline", "series_outline"),
)

# 子技能默认需要的 upstream 键（未配置时仍传 dedupe 后全量，保证兼容）
_SUB_SKILL_UPSTREAM_INCLUDE: Dict[str, Tuple[str, ...]] = {
    "structure-generator": ("projectBrief", "theme", "episodeCount", "creationEntry"),
    "world-builder": ("projectBrief", "structurePlan", "theme", "episodeCount"),
    "dream-indicators": ("structurePlan", "theme", "episodeCount"),
    "world-fixer": ("structurePlan", "validationIssues", "theme", "episodeCount"),
    "character-generator": ("projectBrief", "structurePlan", "theme", "episodeCount"),
    "relationship-weaver": ("projectBrief", "structurePlan", "characterBible", "theme", "episodeCount"),
    "framework-builder": ("projectBrief", "structurePlan", "characterBible", "theme", "episodeCount"),
    "episode-outline-writer": (
        "projectBrief",
        "structurePlan",
        "characterBible",
        "seriesOutline",
        "theme",
        "episodeCount",
    ),
    "hook-planner": ("seriesOutline", "structurePlan", "characterBible", "theme", "episodeCount"),
    "reversal-scheduler": ("seriesOutline", "structurePlan", "theme", "episodeCount"),
    "conflict-advisor": ("seriesOutline", "structurePlan", "characterBible", "theme", "episodeCount"),
    "payment-planner": ("seriesOutline", "structurePlan", "theme", "episodeCount"),
    "psychology-advisor": ("seriesOutline", "characterBible", "theme", "episodeCount"),
    "plan-fixer": ("seriesOutline", "structurePlan", "validationIssues", "theme", "episodeCount"),
    "episode-script-writer": (
        "projectBrief",
        "structurePlan",
        "characterBible",
        "seriesOutline",
        "theme",
        "episodeCount",
    ),
    "from-outline-expander": ("projectBrief", "seriesOutline", "theme", "episodeCount"),
}

_PASS_THROUGH_SCALARS = frozenset(
    {
        "theme",
        "episodeCount",
        "nodeId",
        "creationEntry",
        "validationIssues",
        "stageKey",
        "outlineStageKey",
        "batchFrom",
        "batchTo",
        "scriptFrom",
        "scriptTo",
        "outlineMode",
    }
)


def dedupe_upstream_aliases(upstream: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(upstream, dict):
        return {}
    out = dict(upstream)
    for camel, snake in _ALIAS_GROUPS:
        if camel in out and snake in out and out[camel] == out[snake]:
            del out[snake]
    return out


def pick_upstream_for_sub_skill(
    upstream: Dict[str, Any],
    skill_id: str,
    skill_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """按 sub_skill 裁剪 upstream，减少 Prompt 中无关 artifact 重复。"""
    base = dedupe_upstream_aliases(upstream or {})
    meta = skill_meta or {}
    include_raw = meta.get("upstreamInclude") or meta.get("upstream_include")
    include: Optional[Sequence[str]] = include_raw if include_raw else _SUB_SKILL_UPSTREAM_INCLUDE.get(skill_id)
    if not include:
        return base

    picked: Dict[str, Any] = {}
    for key in include:
        if key in base:
            picked[key] = base[key]
    for key in _PASS_THROUGH_SCALARS:
        if key in base and key not in picked:
            picked[key] = base[key]
    return picked


def summarize_upstream_for_trace(
    upstream: Optional[Dict[str, Any]],
    *,
    node_id: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """轨迹用 upstream 摘要：只保留键名、规模与标量，不存全文。"""
    from apps.creation.pipeline_debug_log import summarize_upstream

    upstream = upstream or {}
    node = node_id or str(upstream.get("nodeId") or "")
    if extra:
        node = node or str(extra.get("fusion_node_id") or extra.get("node_id") or "")
    summary = summarize_upstream(node, upstream)
    for key in _PASS_THROUGH_SCALARS:
        if key in upstream:
            summary[key] = upstream[key]
    if extra:
        summary["traceExtra"] = {
            k: extra[k]
            for k in ("agent_id", "fusion_node_id", "sub_skill_id", "skill_id")
            if k in extra
        }
    return summary
