# -*- coding: utf-8 -*-
"""Fusion references 摘要：钩子库 / 反转模式库 ↔ 武器库技巧联动。"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict, List, Optional

_REVERSAL_TYPE_TO_TECHNIQUE: Dict[str, tuple] = {
    "identity-reveal": ("RV-01", "隐藏身份大揭秘", "表面身份与真实身份完全错位"),
    "relationship-reversal": ("RV-05", "立场突变", "盟友变对手或对手变盟友"),
    "hidden-truth": ("RV-06", "真相倒转", "观众以为的真相被整体推翻"),
    "fortunes-reversal": ("RV-07", "假死/失踪回归", "死亡假象后的强势回归"),
    "villain-twist": ("RV-03", "我方是反派", "最信任者实为幕后黑手"),
    "motivation-change": ("RV-05", "立场突变", "动机或阵营发生根本转变"),
    "other": ("RV-08", "契约/规则翻盘", "利用世界观铁律反杀"),
}

_REVERSAL_TYPE_TO_PATTERN_CATEGORY: Dict[str, str] = {
    "identity-reveal": "身份类反转",
    "relationship-reversal": "关系类反转",
    "hidden-truth": "信息类反转",
    "fortunes-reversal": "命运类反转",
    "villain-twist": "身份类反转",
    "motivation-change": "关系类反转",
    "other": "信息类反转",
}

_INTENSITY_HOOK_CATEGORIES: List[tuple] = [
    (9, ("情绪冲突类", "身份反转类")),
    (7, ("悬念/危机类", "情感震撼类")),
    (5, ("悬疑阴谋类", "对话/台词钩子类")),
    (1, ("设定/世界观类", "复合型/多要素钩子")),
]


def _load_hook_library() -> dict:
    from apps.skill.config.portal.reference_libs import ReferenceLibraryService

    return ReferenceLibraryService.get_json("hook-types-library.json")


@lru_cache(maxsize=1)
def _load_reversal_library() -> dict:
    from apps.skill.config.portal.reference_libs import ReferenceLibraryService

    return ReferenceLibraryService.get_json("reversal-patterns-library.json")


def lookup_hook_type(code: str) -> Optional[dict]:
    c = (code or "").strip()
    if not c:
        return None
    data = _load_hook_library()
    for cat in data.get("categories") or []:
        if not isinstance(cat, dict):
            continue
        category = (cat.get("category") or "").strip()
        for item in cat.get("types") or []:
            if not isinstance(item, dict):
                continue
            if (item.get("code") or "").strip() == c:
                templates = item.get("templateSentences") or []
                return {
                    "code": c,
                    "name": (item.get("nameZh") or c).strip(),
                    "category": category,
                    "effectiveness": item.get("effectiveness"),
                    "hint": (templates[0] if templates else "")[:120],
                }
    return None


def lookup_reversal_pattern(code: str) -> Optional[dict]:
    c = (code or "").strip()
    if not c:
        return None
    data = _load_reversal_library()
    for category, items in (data.get("patternsByCategory") or {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            if (item.get("code") or "").strip() == c:
                return {
                    "code": c,
                    "name": (item.get("patternName") or c).strip(),
                    "category": str(category),
                    "description": (item.get("description") or "")[:200],
                    "bestOccasion": (item.get("bestOccasion") or "")[:120],
                }
    return None


def match_reversal_pattern_for_type(rtype: str) -> Optional[dict]:
    category = _REVERSAL_TYPE_TO_PATTERN_CATEGORY.get(rtype or "other", "信息类反转")
    data = _load_reversal_library()
    items = data.get("patternsByCategory", {}).get(category) or []
    if not isinstance(items, list) or not items:
        for pool in (data.get("patternsByCategory") or {}).values():
            if isinstance(pool, list) and pool:
                items = pool
                break
    if not items:
        return None
    first = items[0] if isinstance(items[0], dict) else {}
    code = (first.get("code") or "").strip()
    if not code:
        return None
    return lookup_reversal_pattern(code)


def suggest_hooks_for_intensity(
    intensity_level: int,
    *,
    theme: str = "",
    limit: int = 3,
) -> List[dict]:
    """按节奏强度段推荐钩子类型（对照 hook-types-library）。"""
    level = max(1, min(10, int(intensity_level or 5)))
    preferred: List[str] = []
    for threshold, cats in _INTENSITY_HOOK_CATEGORIES:
        if level >= threshold:
            preferred = list(cats)
            break
    if not preferred:
        preferred = ["情绪冲突类"]

    theme_key = (theme or "").strip()
    rows: List[dict] = []
    data = _load_hook_library()
    for cat in data.get("categories") or []:
        if not isinstance(cat, dict):
            continue
        category = (cat.get("category") or "").strip()
        if category not in preferred:
            continue
        for item in cat.get("types") or []:
            if not isinstance(item, dict):
                continue
            code = (item.get("code") or "").strip()
            if not code:
                continue
            themes = item.get("applicableThemes") or []
            if theme_key and themes and theme_key not in themes:
                continue
            templates = item.get("templateSentences") or []
            rows.append(
                {
                    "code": code,
                    "name": (item.get("nameZh") or code).strip(),
                    "category": category,
                    "effectiveness": item.get("effectiveness") or 0,
                    "hint": (templates[0] if templates else "")[:100],
                }
            )
    if not rows:
        rows = summarize_hook_types(limit=limit * 2)
    rows.sort(key=lambda r: -(r.get("effectiveness") or 0))
    return rows[:limit]


def resolve_hook_labels(codes: List[str]) -> List[dict]:
    out: List[dict] = []
    for code in codes or []:
        row = lookup_hook_type(str(code))
        if row:
            out.append(row)
    return out


def _episode_in_range(episode: int, start: Optional[int], end: Optional[int]) -> bool:
    if start is None or end is None:
        return False
    return start <= int(episode) <= end


def enrich_rhythm_block_view(
    block: dict,
    *,
    reversals: Optional[List[dict]] = None,
    theme: str = "",
) -> dict:
    """节奏段展示：钩子推荐 + 段内反转联动。"""
    if not isinstance(block, dict):
        return block
    out = dict(block)
    level = int(out.get("intensityLevel") or 5)
    start = out.get("episodeStart")
    end = out.get("episodeEnd")

    codes = out.get("suggestedHookCodes") or []
    if not isinstance(codes, list):
        codes = []
    codes = [str(c).strip() for c in codes if str(c).strip()]
    if not codes:
        codes = [h["code"] for h in suggest_hooks_for_intensity(level, theme=theme, limit=3)]
    out["suggestedHookCodes"] = codes
    out["suggestedHooks"] = resolve_hook_labels(codes)

    linked: List[dict] = []
    for rev in reversals or []:
        if not isinstance(rev, dict):
            continue
        ep = rev.get("episodeNumber")
        if ep is None:
            continue
        if _episode_in_range(int(ep), start, end):
            linked.append(
                {
                    "episodeNumber": int(ep),
                    "reversalTypeLabel": rev.get("reversalTypeLabel") or rev.get("reversalType"),
                    "patternCode": rev.get("patternCode") or rev.get("reversalCode"),
                    "patternName": rev.get("patternName"),
                    "techniqueCode": rev.get("techniqueCode"),
                }
            )
    out["linkedReversals"] = sorted(linked, key=lambda r: r.get("episodeNumber") or 0)
    return out


def backfill_reversal_codes(reversals: List[dict]) -> List[dict]:
    """为缺少 reversalCode 的反转点回填参考库模式代码。"""
    out: List[dict] = []
    for rev in reversals or []:
        if not isinstance(rev, dict):
            continue
        item = dict(rev)
        if not (item.get("reversalCode") or item.get("patternCode")):
            enriched = enrich_reversal_point(item)
            code = enriched.get("patternCode")
            if code:
                item["reversalCode"] = code
        out.append(item)
    return out


def backfill_rhythm_hook_codes(
    blocks: List[dict],
    *,
    theme: str = "",
) -> List[dict]:
    """为缺少 suggestedHookCodes 的节奏段回填钩子推荐。"""
    out: List[dict] = []
    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        item = dict(block)
        codes = item.get("suggestedHookCodes") or []
        if not isinstance(codes, list) or not codes:
            level = int(item.get("intensityLevel") or 5)
            item["suggestedHookCodes"] = [
                h["code"] for h in suggest_hooks_for_intensity(level, theme=theme, limit=3)
            ]
        out.append(item)
    return out


def enrich_reversal_point(rev: dict) -> dict:
    if not isinstance(rev, dict):
        return {}
    out = dict(rev)
    rtype = (out.get("reversalType") or out.get("type") or "other").strip()
    tech = _REVERSAL_TYPE_TO_TECHNIQUE.get(rtype, _REVERSAL_TYPE_TO_TECHNIQUE["other"])
    out["techniqueCode"] = tech[0]
    out["techniqueLabel"] = tech[1]
    out["techniqueHint"] = tech[2]

    pattern_code = (out.get("reversalCode") or out.get("patternCode") or "").strip()
    pattern = lookup_reversal_pattern(pattern_code) if pattern_code else None
    if not pattern:
        pattern = match_reversal_pattern_for_type(rtype)
    if pattern:
        out["patternCode"] = pattern.get("code")
        out["patternName"] = pattern.get("name")
        out["patternDescription"] = pattern.get("description")
        out["patternBestOccasion"] = pattern.get("bestOccasion")
    return out


def summarize_hook_types(*, limit: int = 14) -> List[dict]:
    rows: List[dict] = []
    data = _load_hook_library()
    for cat in data.get("categories") or []:
        if not isinstance(cat, dict):
            continue
        category = (cat.get("category") or "").strip()
        for item in cat.get("types") or []:
            if not isinstance(item, dict):
                continue
            code = (item.get("code") or "").strip()
            if not code:
                continue
            templates = item.get("templateSentences") or []
            rows.append(
                {
                    "code": code,
                    "name": (item.get("nameZh") or code).strip(),
                    "category": category,
                    "effectiveness": item.get("effectiveness"),
                    "hint": (templates[0] if templates else "")[:100],
                }
            )
    rows.sort(key=lambda r: -(r.get("effectiveness") or 0))
    return rows[:limit]


def summarize_reversal_patterns(*, limit: int = 12) -> List[dict]:
    rows: List[dict] = []
    data = _load_reversal_library()
    for category, items in (data.get("patternsByCategory") or {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            code = (item.get("code") or "").strip()
            if not code:
                continue
            rows.append(
                {
                    "code": code,
                    "name": (item.get("patternName") or code).strip(),
                    "category": str(category),
                    "description": (item.get("description") or "")[:160],
                    "surpriseLevel": item.get("audienceSurpriseLevel"),
                }
            )
    rows.sort(key=lambda r: -(r.get("surpriseLevel") or 0))
    return rows[:limit]


def build_reference_library_summary() -> dict:
    return {
        "hookTypes": summarize_hook_types(),
        "reversalPatterns": summarize_reversal_patterns(),
    }


def resolve_episode_reference_labels(
    hook_type_code: str = "",
    reversal_code: str = "",
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    hook = lookup_hook_type(hook_type_code)
    if hook:
        out["hookTypeLabel"] = hook.get("name")
        out["hookTypeHint"] = hook.get("hint")
    pattern = lookup_reversal_pattern(reversal_code)
    if pattern:
        out["reversalPatternLabel"] = pattern.get("name")
        out["reversalPatternHint"] = pattern.get("description")
    return out
