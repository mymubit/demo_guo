# -*- coding: utf-8 -*-
"""OutlineAgent：节点 4 大纲（framework / stage / episodes 模式 + sub-plan 校验）。"""
from __future__ import annotations

import logging
from typing import List, Optional

from ..artifact_service import get_artifact, save_artifact
from ..models import Project
from ..outline_enrichment import enrich_outline_payload
from ..workspace.workspace_editor import _mark_skill_has_content, _outline_framework_ready
from .agent_common import (
    build_standard_upstream,
    deep_merge,
    filter_episodes_by_range,
    load_project_brief,
    merge_episodes_by_number,
)
from .agent_llm import run_sub_skill_llm
from .agent_payload import coerce_outline_chunk, extract_fixer_patch, fixer_patch_meaningful, unwrap_llm_payload
from .sub_skill_runner import (
    agent_execution_meta,
    inject_knowledge_upstream,
    mark_executed,
    persist_execution_trace,
)
from .types import AgentResult

logger = logging.getLogger(__name__)

AGENT_ID = "outline"
FUSION_NODE_ID = "node-4-outline"
NODE_INDEX = 4

_FRAMEWORK_SUB_SKILLS = (
    "framework-builder",
    "hook-planner",
    "reversal-scheduler",
    "conflict-advisor",
    "payment-planner",
    "psychology-advisor",
)


def _seed_series_outline(project: Project, brief: dict) -> dict:
    existing = get_artifact(project, "series_outline") or {}
    if isinstance(existing, dict) and existing:
        return dict(existing)
    return {
        "nodeId": FUSION_NODE_ID,
        "projectId": str(project.id),
        "totalEpisodes": int(project.episode_count or brief.get("episodeCount") or 80),
    }


def _merge_framework_chunk(outline: dict, sub_skill_id: str, raw: object) -> dict:
    chunk = unwrap_llm_payload(sub_skill_id, raw)
    if sub_skill_id == "framework-builder":
        chunk = coerce_outline_chunk(chunk)
    if sub_skill_id in {"hook-planner", "reversal-scheduler", "conflict-advisor", "payment-planner", "psychology-advisor"}:
        creative = chunk.get("creativePlan") if isinstance(chunk.get("creativePlan"), dict) else chunk
        if isinstance(creative, dict) and creative:
            plan = dict(outline.get("creativePlan") or {})
            outline["creativePlan"] = deep_merge(plan, creative)
        for key in ("stageBlocks", "roughOutline", "stageIndex", "keyHighlights"):
            if chunk.get(key) is not None:
                outline[key] = chunk[key]
        return outline
    return deep_merge(outline, coerce_outline_chunk(chunk))


def _run_plan_validator(project: Project, outline: dict) -> dict:
    from apps.creation.validators import validate_plan

    expected = int(outline.get("totalEpisodes") or project.episode_count or 0) or None
    result = validate_plan(outline, expected_episodes=expected)
    return result.to_dict()


def _resolve_outline_mode(
    outline: dict,
    outline_mode: Optional[str],
    script_from: Optional[int],
    script_to: Optional[int],
) -> str:
    mode = (outline_mode or "").strip()
    if mode in {"framework", "stage_framework", "episodes"}:
        return mode
    if script_from is not None and script_to is not None:
        return "episodes"
    if not _outline_framework_ready(outline):
        return "framework"
    return "episodes"


def run_outline_agent(
    project: Project,
    *,
    node_index: int = NODE_INDEX,
    script_from: Optional[int] = None,
    script_to: Optional[int] = None,
    outline_mode: Optional[str] = None,
    outline_stage_key: Optional[str] = None,
    **_kwargs,
) -> AgentResult:
    executed: List[str] = []
    errors: List[str] = []

    brief = load_project_brief(project)
    structure = get_artifact(project, "structure_plan") or {}
    character_bible = get_artifact(project, "character_bible") or {}
    upstream = build_standard_upstream(
        project,
        brief,
        structure=structure,
        character_bible=character_bible,
    )
    outline = _seed_series_outline(project, brief)
    mode = _resolve_outline_mode(outline, outline_mode, script_from, script_to)

    try:
        upstream = inject_knowledge_upstream(AGENT_ID, upstream, project)
        mark_executed(executed, "reference-injector")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[OutlineAgent] reference-injector skipped: %s", exc)

    if mode in {"framework", "stage_framework"}:
        llm_upstream = {
            **upstream,
            "seriesOutline": outline,
            "series_outline": outline,
        }
        if mode == "stage_framework" and outline_stage_key:
            llm_upstream["stageKey"] = outline_stage_key
            llm_upstream["outlineStageKey"] = outline_stage_key
        for sub_skill_id in _FRAMEWORK_SUB_SKILLS:
            try:
                raw = run_sub_skill_llm(
                    project,
                    agent_id=AGENT_ID,
                    fusion_node_id=FUSION_NODE_ID,
                    sub_skill_id=sub_skill_id,
                    upstream=llm_upstream,
                )
                outline = _merge_framework_chunk(outline, sub_skill_id, raw)
                llm_upstream = {**llm_upstream, "seriesOutline": outline, "series_outline": outline}
                mark_executed(executed, sub_skill_id)
            except Exception as exc:  # noqa: BLE001
                logger.exception("[OutlineAgent] sub_skill=%s failed", sub_skill_id)
                errors.append(f"{sub_skill_id}: {exc}")

    if mode == "episodes":
        ep_from = int(script_from or 1)
        ep_to = int(script_to or ep_from)
        llm_upstream = {
            **upstream,
            "seriesOutline": outline,
            "series_outline": outline,
            "episodeFrom": ep_from,
            "episodeTo": ep_to,
            "fromEpisode": ep_from,
            "toEpisode": ep_to,
        }
        try:
            raw = run_sub_skill_llm(
                project,
                agent_id=AGENT_ID,
                fusion_node_id=FUSION_NODE_ID,
                sub_skill_id="episode-outline-writer",
                upstream=llm_upstream,
            )
            chunk = coerce_outline_chunk(raw)
            episodes = chunk.get("episodes") or []
            if len(episodes) > (ep_to - ep_from + 1):
                logger.warning(
                    "[OutlineAgent] episode-outline-writer returned %s episodes; clamping to %s-%s",
                    len(episodes),
                    ep_from,
                    ep_to,
                )
            outline = merge_episodes_by_number(
                outline,
                episodes,
                episode_from=ep_from,
                episode_to=ep_to,
            )
            mark_executed(executed, "episode-outline-writer")
        except Exception as exc:  # noqa: BLE001
            logger.exception("[OutlineAgent] episode-outline-writer failed")
            errors.append(f"episode-outline-writer: {exc}")

    validation: dict = {}
    try:
        outline = enrich_outline_payload(
            outline,
            structure_plan=structure,
            character_bible=character_bible,
            project_brief=brief,
            theme=project.theme or "",
            total_episodes=int(outline.get("totalEpisodes") or project.episode_count or 0) or None,
        )
        validation = _run_plan_validator(project, outline)
        mark_executed(executed, "plan-validator")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[OutlineAgent] plan-validator skipped: %s", exc)
        validation = {"passed": True, "issues": []}

    if not validation.get("passed"):
        issues = list(validation.get("issues") or [])
        try:
            fix_raw = run_sub_skill_llm(
                project,
                agent_id=AGENT_ID,
                fusion_node_id=FUSION_NODE_ID,
                sub_skill_id="plan-fixer",
                upstream={
                    **upstream,
                    "seriesOutline": outline,
                    "validationIssues": issues,
                },
                system_hint="根据 validationIssues 修复 seriesOutline，输出完整 JSON（含 creativePlan）。",
            )
            patch = extract_fixer_patch("plan-fixer", fix_raw)
            if fixer_patch_meaningful(patch):
                if mode == "episodes":
                    fix_eps = patch.get("episodes")
                    if isinstance(fix_eps, list):
                        patch = dict(patch)
                        patch["episodes"] = filter_episodes_by_range(fix_eps, ep_from, ep_to)
                outline = deep_merge(outline, patch)
                mark_executed(executed, "plan-fixer")
                validation = _run_plan_validator(project, outline)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[OutlineAgent] plan-fixer skipped: %s", exc)

    outline["planValidationLog"] = {
        "passed": bool(validation.get("passed")),
        "issues": list(validation.get("issues") or []),
        "checker": "sub-plan",
    }
    if not validation.get("passed") and not errors:
        issues = validation.get("issues") or []
        if issues:
            errors.append("; ".join(str(i) for i in issues[:3]))

    try:
        outline.setdefault("projectId", str(project.id))
        outline.setdefault("totalEpisodes", int(project.episode_count or brief.get("episodeCount") or 80))
        save_artifact(project, "series_outline", outline)
        filled = len(
            [
                e
                for e in (outline.get("episodes") or [])
                if isinstance(e, dict) and (e.get("oneLineSummary") or "").strip()
            ]
        )
        if mode == "framework":
            summary = "集纲框架已生成"
        else:
            summary = f"{filled} 集大纲"
        _mark_skill_has_content(project, node_index, summary)
    except Exception as exc:  # noqa: BLE001
        logger.exception("[OutlineAgent] finalize failed")
        errors.append(str(exc))

    persist_execution_trace(project, node_index, AGENT_ID, executed)
    status = "completed" if not errors else "error"
    return AgentResult(
        agent_id=AGENT_ID,
        status=status,
        outputs={"series_outline": outline, "artifact_key": "series_outline"},
        errors=errors,
        meta={
            **agent_execution_meta(AGENT_ID, executed, node_index=node_index),
            "outline_mode": mode,
        },
    )
