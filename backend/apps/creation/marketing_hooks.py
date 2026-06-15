# -*- coding: utf-8 -*-
"""clip-hook-generator：投流切片前 3 秒钩子文案（规则 + 参考库）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .reference_library import lookup_hook_type, summarize_hook_types


def _first_episode(outline: dict) -> Optional[dict]:
    eps = outline.get("episodes") or []
    sorted_eps = sorted(
        [e for e in eps if isinstance(e, dict) and e.get("episodeNumber") is not None],
        key=lambda x: int(x.get("episodeNumber") or 0),
    )
    return sorted_eps[0] if sorted_eps else None


def _hook_line_from_episode(ep: dict) -> str:
    for key in ("hook", "openingHook", "oneLineSummary"):
        val = (ep.get(key) or "").strip()
        if len(val) >= 8:
            return val[:120]
    return ""


def build_clip_hooks(
    *,
    brief: Optional[dict] = None,
    outline: Optional[dict] = None,
    structure_plan: Optional[dict] = None,
    limit: int = 5,
) -> List[str]:
    hooks: List[str] = []
    seen: set[str] = set()

    def add(text: str) -> None:
        t = (text or "").strip()
        if not t or t in seen or len(t) < 6:
            return
        seen.add(t)
        hooks.append(t)

    ep1 = _first_episode(outline or {})
    if ep1:
        code = (ep1.get("hookTypeCode") or "").strip()
        row = lookup_hook_type(code) if code else None
        if row:
            hint = (row.get("hint") or row.get("name") or "")[:80]
            add(f"第1集前3秒 · {row.get('name') or code}：{hint}")
        line = _hook_line_from_episode(ep1)
        if line:
            add(f"第1集开场：{line[:80]}")

    brief = brief or {}
    core = (brief.get("coreHook") or "").strip()
    if core:
        add(f"投流切片：{core[:80]}")

    structure = structure_plan or {}
    rhythm = structure.get("rhythmCurve") or []
    if rhythm and isinstance(rhythm[0], dict):
        block = rhythm[0]
        for item in block.get("suggestedHooks") or []:
            if isinstance(item, dict):
                name = (item.get("name") or "").strip()
                hint = (item.get("hint") or "")[:60]
                if name:
                    add(f"节奏段推荐 · {name}：{hint}")
        for code in block.get("suggestedHookCodes") or []:
            row = lookup_hook_type(str(code))
            if row:
                add(f"结构推荐 · {row.get('name')}：{(row.get('hint') or '')[:60]}")

    for row in summarize_hook_types(limit=4):
        name = (row.get("name") or "").strip()
        hint = (row.get("hint") or "")[:60]
        if name:
            add(f"爆款钩子 · {name}：{hint}")

    revs = structure.get("keyReversalPoints") or []
    if revs and isinstance(revs[0], dict):
        rev = revs[0]
        ep = rev.get("episodeNumber")
        desc = (rev.get("description") or rev.get("patternName") or "")[:50]
        if desc:
            add(f"第{ep or 1}集反转切片：{desc}")

    return hooks[:limit]


def enrich_marketing_kit(
    kit: dict,
    *,
    brief: Optional[dict] = None,
    outline: Optional[dict] = None,
    structure_plan: Optional[dict] = None,
) -> Dict[str, Any]:
    out = dict(kit or {})
    generated = build_clip_hooks(brief=brief, outline=outline, structure_plan=structure_plan)
    existing = [str(h).strip() for h in (out.get("clipHooks") or []) if str(h).strip()]
    merged: List[str] = []
    seen: set[str] = set()
    for item in existing + generated:
        if item and item not in seen:
            seen.add(item)
            merged.append(item)
    out["clipHooks"] = merged[:8]
    out["clipHookSource"] = "clip-hook-generator"
    return out
