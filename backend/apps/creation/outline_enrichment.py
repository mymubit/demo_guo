# -*- coding: utf-8 -*-
"""分集大纲产物：规则补全 stageIndex / creativePlan / keyHighlights。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .conflict_advisor import merge_conflict_into_creative_plan
from .payment_planner import merge_payment_into_creative_plan
from .psychology_advisor import merge_psychology_into_creative_plan
from .outline_skeleton import _stage_index_from_blocks, build_six_stage_blocks


from .display.structure_display import _REVERSAL_LABELS


_PAYWALL_MARKER_LABELS = {
    "paywall": "付费卡点",
    "strong-hook": "强钩子",
    "cliffhanger": "悬念卡点",
}


def _label_reversal_type(rtype: str) -> str:
    return _REVERSAL_LABELS.get(rtype, rtype)


def _enrich_creative_plan_labels(plan: dict) -> dict:
    if not isinstance(plan, dict):
        return plan
    out = dict(plan)
    checkpoints = []
    for pt in out.get("paymentCheckpoints") or []:
        if not isinstance(pt, dict):
            continue
        marker = pt.get("marker") or ""
        checkpoints.append(
            {
                **pt,
                "markerLabel": _PAYWALL_MARKER_LABELS.get(marker, marker) if marker else "",
            }
        )
    if checkpoints:
        out["paymentCheckpoints"] = checkpoints

    reversals = []
    for rev in out.get("reversalSchedule") or []:
        if not isinstance(rev, dict):
            continue
        rtype = rev.get("type") or rev.get("reversalType") or "other"
        reversals.append(
            {
                **rev,
                "type": rtype,
                "typeLabel": rev.get("typeLabel") or _label_reversal_type(str(rtype)),
            }
        )
    if reversals:
        out["reversalSchedule"] = reversals
    return out


def _default_creative_plan(total_eps: int, structure_plan: Optional[dict] = None) -> dict:
    checkpoints: List[dict] = []
    if total_eps >= 30:
        for ep in (8, 9, 10):
            if ep <= total_eps:
                checkpoints.append(
                    {
                        "episode": ep,
                        "marker": "paywall",
                        "markerLabel": "付费卡点",
                        "description": f"第{ep}集付费/强卡点",
                    }
                )
    reversals = []
    if isinstance(structure_plan, dict):
        from .reference_library import enrich_reversal_point

        for rev in structure_plan.get("keyReversalPoints") or []:
            if not isinstance(rev, dict):
                continue
            ep = rev.get("episodeNumber")
            desc = (rev.get("description") or "")[:120]
            if ep and desc:
                rtype = rev.get("reversalType", "other")
                enriched = enrich_reversal_point(
                    {
                        "episode": ep,
                        "type": rtype,
                        "note": desc,
                        "reversalCode": rev.get("reversalCode") or rev.get("patternCode"),
                    }
                )
                reversals.append(
                    {
                        "episode": ep,
                        "type": rtype,
                        "typeLabel": _label_reversal_type(str(rtype)),
                        "note": desc,
                        "techniqueCode": enriched.get("techniqueCode"),
                        "techniqueLabel": enriched.get("techniqueLabel"),
                        "patternCode": enriched.get("patternCode"),
                        "patternName": enriched.get("patternName"),
                    }
                )

    plan = {
        "hookDiversity": {
            "maxSameTypeInRow": 2,
            "forbidAdjacentSameStrength": True,
            "requiredTypes": ["HOOK-SLAP", "HOOK-QUESTION", "HOOK-CONFLICT"],
        },
        "paymentCheckpoints": checkpoints,
        "reversalSchedule": reversals[:12],
        "psychologyStrategy": {
            "dominantArchetype": "efficient-satisfaction",
            "notes": "每 3 集小波动，每 10 集大高潮；前 10 集建立共情与悬念链。",
        },
    }
    return _enrich_creative_plan_labels(plan)


def _key_highlights_from_structure(structure_plan: Optional[dict], total_eps: int) -> List[dict]:
    highlights: List[dict] = []
    if not isinstance(structure_plan, dict):
        return highlights
    for rev in structure_plan.get("keyReversalPoints") or []:
        if not isinstance(rev, dict):
            continue
        ep = rev.get("episodeNumber")
        desc = (rev.get("description") or "").strip()
        if ep and desc:
            highlights.append(
                {
                    "episode": ep,
                    "type": "reversal",
                    "title": desc[:48],
                    "description": desc[:200],
                }
            )
    for block in structure_plan.get("rhythmCurve") or []:
        if not isinstance(block, dict):
            continue
        er = block.get("episodeRange") or ""
        if er.endswith("-10") or "10" in str(er):
            highlights.append(
                {
                    "episode": 10,
                    "type": "rhythm-peak",
                    "title": f"节奏峰值 · 第{er}集",
                    "description": (block.get("notes") or "")[:200],
                }
            )
    if not highlights and total_eps >= 10:
        highlights.append(
            {
                "episode": 10,
                "type": "milestone",
                "title": "第一幕高潮",
                "description": "前十集完成核心冲突建立与首次大反转。",
            }
        )
    return highlights[:8]


def enrich_outline_payload(
    payload: dict,
    *,
    structure_plan: Optional[dict] = None,
    character_bible: Optional[dict] = None,
    project_brief: Optional[dict] = None,
    theme: str = "",
    total_episodes: Optional[int] = None,
) -> dict:
    if not isinstance(payload, dict):
        return payload

    total = int(payload.get("totalEpisodes") or total_episodes or 80)
    blocks = payload.get("stageBlocks") or []
    if isinstance(blocks, list) and len(blocks) < 6:
        six_blocks = build_six_stage_blocks(total, (structure_plan or {}).get("sixStagePlan"))
        existing_by_key = {
            (b.get("key") or f"stage{b.get('stageIndex')}"): b
            for b in blocks
            if isinstance(b, dict)
        }
        merged_blocks: List[dict] = []
        for block in six_blocks:
            key = block.get("key") or ""
            prev = existing_by_key.get(key) or {}
            merged_blocks.append(
                {
                    **block,
                    "roughOutline": (prev.get("roughOutline") or block.get("roughOutline") or "")[:3000],
                }
            )
        payload["stageBlocks"] = merged_blocks
        blocks = merged_blocks

    if not payload.get("stageIndex") and blocks:
        payload["stageIndex"] = _stage_index_from_blocks(blocks)

    creative = payload.get("creativePlan")
    default_plan = _default_creative_plan(total, structure_plan)
    if isinstance(creative, dict):
        merged = _deep_merge_creative(default_plan, creative)
        if not creative.get("paymentCheckpoints"):
            merged["paymentCheckpoints"] = default_plan.get("paymentCheckpoints") or []
        if not creative.get("reversalSchedule"):
            merged["reversalSchedule"] = default_plan.get("reversalSchedule") or []
        if not creative.get("psychologyStrategy"):
            merged["psychologyStrategy"] = default_plan.get("psychologyStrategy") or {}
        if not creative.get("hookDiversity"):
            merged["hookDiversity"] = default_plan.get("hookDiversity") or {}
        payload["creativePlan"] = _enrich_creative_plan_labels(merged)
    else:
        payload["creativePlan"] = _enrich_creative_plan_labels(default_plan)

    payload["creativePlan"] = merge_conflict_into_creative_plan(
        payload.get("creativePlan") or {},
        structure_plan=structure_plan,
        character_bible=character_bible,
        total_episodes=total,
    )
    payload["creativePlan"] = merge_payment_into_creative_plan(
        payload.get("creativePlan") or {},
        total_episodes=total,
        structure_plan=structure_plan,
    )
    payload["creativePlan"] = merge_psychology_into_creative_plan(
        payload.get("creativePlan") or {},
        theme=theme,
        project_brief=project_brief,
        structure_plan=structure_plan,
        total_episodes=total,
    )

    if not payload.get("keyHighlights"):
        payload["keyHighlights"] = _key_highlights_from_structure(structure_plan, total)

    payload.setdefault("nodeId", "node-4-outline")
    payload.setdefault("nodeName", "大纲与创作规划节点")
    payload["totalEpisodes"] = total
    return payload


def _deep_merge_creative(base: dict, patch: dict) -> dict:
    out = dict(base)
    for key, val in (patch or {}).items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = {**out[key], **val}
        elif val:
            out[key] = val
    return out
