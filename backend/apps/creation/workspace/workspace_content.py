# -*- coding: utf-8 -*-
"""工作台内容来源判定：区分用户确认参数 vs Agent 生成产物，避免误报「缺失」。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from ..artifact_service import get_artifact, save_artifact
from ..models import CreationNode, Project
from ..schema_mappers import enrich_brief_from_form_seed
from ..trend_formula import trend_formula_has_internal_refs
from ..workspace.artifact_keys import artifact_key_for_node

CONTENT_EMPTY = "empty"
CONTENT_USER_CONFIRMED = "user_confirmed"
CONTENT_SKELETON = "skeleton"
CONTENT_AGENT_GENERATED = "agent_generated"
CONTENT_DRAFT = "draft"

_AGENT_READY_KINDS = frozenset({CONTENT_AGENT_GENERATED})


def _trend_formula_needs_story_refresh(brief: dict, trend: Optional[dict]) -> bool:
    if not isinstance(trend, dict):
        return True
    if trend_formula_has_internal_refs(trend):
        return True
    highlights = trend.get("highlights") or []
    if any("参考钩子" in str(item) for item in highlights):
        return True
    from .workspace_editor import _story_brief_from_payload

    story = _story_brief_from_payload(brief)
    has_user_story = any(
        (story.get(key) or "").strip()
        for key in ("idea", "openingHooks", "coreConflict")
    )
    if has_user_story and not (trend.get("projectHook") or trend.get("projectIdea")):
        return True
    return False


def ensure_brief_seed_enriched(project: Project) -> Optional[dict]:
    """旧项目回填：将用户已填故事策划映射为 trendFormula / writingBrief。"""
    from ..artifact_readiness import project_brief_ready
    from ..schema_mappers import build_project_brief

    brief = get_artifact(project, "project_brief")
    if not isinstance(brief, dict) or not brief:
        if not project_brief_ready(project):
            return None
        brief = build_project_brief(project)
        save_artifact(project, "project_brief", brief)
    trend = brief.get("trendFormula")
    if (
        brief.get("seedEnriched")
        and trend
        and brief.get("writingBrief")
        and not _trend_formula_needs_story_refresh(brief, trend)
    ):
        return brief
    enriched = enrich_brief_from_form_seed(brief, project, submit_data={})
    if enriched != brief:
        save_artifact(project, "project_brief", enriched)
    return enriched


def _outline_filled_episode_count(payload: dict) -> int:
    count = 0
    for ep in payload.get("episodes") or []:
        if not isinstance(ep, dict):
            continue
        summary = (ep.get("oneLineSummary") or ep.get("summary") or "").strip()
        if summary:
            count += 1
    return count


def skill_content_kind(
    node_index: int,
    payload: Optional[dict],
    *,
    has_content: bool,
    node_status: str = CreationNode.STATUS_PENDING,
) -> str:
    if not has_content:
        return CONTENT_EMPTY

    data = payload if isinstance(payload, dict) else {}

    if node_index == 1:
        if data.get("agentEnriched"):
            return CONTENT_AGENT_GENERATED
        if data.get("seedEnriched") or (
            (data.get("coreHook") or data.get("coreIdea") or "").strip() and (data.get("theme") or "").strip()
        ):
            return CONTENT_USER_CONFIRMED
        return CONTENT_AGENT_GENERATED if node_status == CreationNode.STATUS_COMPLETED else CONTENT_USER_CONFIRMED

    if node_index == 3:
        from ..display.character_display import build_character_bible_view

        if build_character_bible_view(data).get("characterCount", 0) <= 0:
            return CONTENT_EMPTY
        if node_status == CreationNode.STATUS_COMPLETED:
            return CONTENT_AGENT_GENERATED
        return CONTENT_DRAFT

    if node_index == 4:
        if _outline_filled_episode_count(data) > 0:
            return CONTENT_AGENT_GENERATED
        if data.get("skeletonReady") or data.get("stageBlocks"):
            return CONTENT_SKELETON

    if node_status == CreationNode.STATUS_COMPLETED:
        return CONTENT_AGENT_GENERATED
    if has_content:
        return CONTENT_DRAFT
    return CONTENT_EMPTY


def count_agent_ready_skills(skills: list) -> int:
    return sum(1 for s in skills if s.get("content_kind") in _AGENT_READY_KINDS)


def should_emit_quality_alert(
    node_index: int,
    alert_code: str,
    *,
    node_status: str = CreationNode.STATUS_PENDING,
    payload: Optional[dict] = None,
    content_kind: str = CONTENT_EMPTY,
) -> bool:
    """仅 Agent 已执行或确有用户遗漏时向 C 端展示告警。"""
    if alert_code == "brief-incomplete":
        return False

    if alert_code == "character-gate":
        return node_status == CreationNode.STATUS_COMPLETED

    if alert_code == "outline-summary-gap":
        return node_status == CreationNode.STATUS_COMPLETED or content_kind == CONTENT_AGENT_GENERATED

    if alert_code == "episode-gate":
        data = payload if isinstance(payload, dict) else {}
        return bool(data.get("episodes"))

    if alert_code.startswith("verify-"):
        return True

    if alert_code == "creator-quality-guard":
        return node_status == CreationNode.STATUS_COMPLETED

    return True


def get_node_payload(project: Project, node_index: int) -> dict:
    key = artifact_key_for_node(node_index)
    if not key:
        return {}
    payload = get_artifact(project, key)
    return payload if isinstance(payload, dict) else {}


def _same_gate_issues(left: Any, right: Any) -> bool:
    return [str(item) for item in (left or [])] == [str(item) for item in (right or [])]


def resolve_character_gate_log(payload: Optional[dict]) -> dict:
    """实时人设 gate 与 artifact 中人工确认状态合并。"""
    from ..character_gate import run_character_gate

    data = payload if isinstance(payload, dict) else {}
    fresh = run_character_gate(data)
    stored = data.get("characterGateLog") or {}
    if (
        not fresh.get("passed")
        and stored.get("userAcknowledgedAt")
        and _same_gate_issues(stored.get("issues"), fresh.get("issues"))
    ):
        return {**fresh, "userAcknowledgedAt": stored["userAcknowledgedAt"]}
    return fresh
