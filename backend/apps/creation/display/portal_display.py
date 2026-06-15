# -*- coding: utf-8 -*-
"""C 端工作台/作品页展示过滤：隐藏内部校验、武器库与方法论字段。"""
from __future__ import annotations

from typing import Any, Dict, List

_REVERSAL_INTERNAL_KEYS = frozenset(
    {
        "reversalCode",
        "patternCode",
        "patternName",
        "patternDescription",
        "techniqueCode",
        "techniqueLabel",
        "techniqueHint",
    }
)

_RHYTHM_INTERNAL_KEYS = frozenset({"suggestedHookCodes", "suggestedHooks"})


def portal_gate_log(log: dict | None) -> dict:
    """质检日志：通过时仅状态；失败时最多 5 条可行动 issues。"""
    if not isinstance(log, dict):
        return {}
    if log.get("skipped"):
        return {"passed": None, "skipped": True}
    if log.get("passed"):
        return {"passed": True, "skipped": False}
    return {
        "passed": False,
        "skipped": False,
        "issues": [str(i) for i in (log.get("issues") or []) if str(i).strip()][:5],
    }


def portal_sanitize_reversal(rev: dict | None) -> dict:
    if not isinstance(rev, dict):
        return {}
    out = {k: v for k, v in rev.items() if k not in _REVERSAL_INTERNAL_KEYS}
    linked = []
    for item in out.get("linkedReversals") or []:
        if not isinstance(item, dict):
            continue
        ep = item.get("episodeNumber")
        if ep is not None:
            linked.append({"episodeNumber": ep})
    if linked:
        out["linkedReversals"] = linked
    elif "linkedReversals" in out:
        out.pop("linkedReversals", None)
    return out


def portal_sanitize_rhythm_block(block: dict | None) -> dict:
    if not isinstance(block, dict):
        return {}
    out = {k: v for k, v in block.items() if k not in _RHYTHM_INTERNAL_KEYS}
    linked = []
    for item in out.get("linkedReversals") or []:
        if not isinstance(item, dict):
            continue
        ep = item.get("episodeNumber")
        if ep is not None:
            linked.append({"episodeNumber": ep})
    if linked:
        out["linkedReversals"] = linked
    elif "linkedReversals" in out:
        out.pop("linkedReversals", None)
    return out


def portal_sanitize_structure_plan_view(view: dict | None) -> dict:
    if not isinstance(view, dict):
        return {}
    out = dict(view)
    out.pop("referenceLibrary", None)
    out["worldValidationLog"] = portal_gate_log(out.get("worldValidationLog"))
    out["keyReversalPoints"] = [
        portal_sanitize_reversal(r) for r in (out.get("keyReversalPoints") or []) if isinstance(r, dict)
    ]
    out["rhythmCurve"] = [
        portal_sanitize_rhythm_block(b) for b in (out.get("rhythmCurve") or []) if isinstance(b, dict)
    ]
    return out


def portal_sanitize_character_bible_view(view: dict | None) -> dict:
    if not isinstance(view, dict):
        return {}
    out = dict(view)
    out.pop("archetypeCodes", None)
    out.pop("archetypeIndex", None)
    out.pop("creativeDna", None)
    chars = []
    for char in out.get("characters") or []:
        if not isinstance(char, dict):
            continue
        row = dict(char)
        row.pop("archetypeCode", None)
        chars.append(row)
    out["characters"] = chars
    return out


def portal_sanitize_review_block(review: dict | None) -> dict | None:
    if not isinstance(review, dict):
        return None
    out = dict(review)
    plot = out.get("plotStructure") if isinstance(out.get("plotStructure"), dict) else None
    if plot:
        out["plotStructure"] = {
            "passed": plot.get("passed"),
            "issues": [str(i) for i in (plot.get("issues") or []) if str(i).strip()][:4],
        }
    quality = out.get("qualityGuard") if isinstance(out.get("qualityGuard"), dict) else None
    if quality:
        out["qualityGuard"] = {
            "passed": quality.get("passed"),
            "skipped": quality.get("skipped"),
            "assessments": [str(i) for i in (quality.get("assessments") or []) if str(i).strip()][:4],
            "issues": [str(i) for i in (quality.get("issues") or []) if str(i).strip()][:4],
        }
    return out


def portal_sanitize_script_episode(ep: dict) -> dict:
    if not isinstance(ep, dict):
        return {}
    out = dict(ep)
    gate = portal_gate_log(out.get("gateLog") if isinstance(out.get("gateLog"), dict) else {})
    out["gateLog"] = gate
    out["gatePassed"] = gate.get("passed") if gate else out.get("gatePassed")
    return out


def portal_execution_run(run: dict | None) -> dict | None:
    """C 端仅保留耗时，不暴露子技能 trace / 产出 key 等。"""
    if not isinstance(run, dict):
        return None
    ms = run.get("duration_ms")
    if ms is None:
        return None
    return {"duration_ms": ms}


def portal_strip_agent_block(block: dict | None) -> dict | None:
    """移除 executionTrace / executionRun，仅保留 durationMs。"""
    if not isinstance(block, dict):
        return None
    out = dict(block)
    out.pop("executionTrace", None)
    run = out.pop("executionRun", None)
    if isinstance(run, dict):
        compact = portal_execution_run(run)
        if compact:
            out["durationMs"] = compact["duration_ms"]
    return out
