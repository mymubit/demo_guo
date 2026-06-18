# -*- coding: utf-8 -*-
"""smart-search：站内参考库关键词/标签检索（规则层）。"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

from .theme_recommender import _theme_templates


_BUILTIN_S_GRADE_CATALOG: dict[str, list[dict[str, Any]]] = {
    "scripts": [
        {
            "id": "builtin-wrong-marriage",
            "title": "错嫁后我逆风翻盘",
            "grade": "S",
            "genre": "错嫁 甜宠 逆袭",
            "platform": "builtin",
            "path": "",
            "enabled": True,
        }
    ]
}


@lru_cache(maxsize=1)
def _s_grade_catalog() -> dict:
    try:
        from apps.skill.config.portal.reference_libs import ReferenceLibraryService

        data = ReferenceLibraryService.get_json("s-grade-catalog.json")
        if data:
            return data
    except Exception:  # noqa: BLE001
        pass
    return _BUILTIN_S_GRADE_CATALOG


def _tokens(query: str) -> List[str]:
    q = (query or "").strip().lower()
    if not q:
        return []
    parts = re.split(r"[\s,，、/|+]+", q)
    return [p for p in parts if len(p) >= 2]


def _score_text(blob: str, tokens: List[str]) -> int:
    if not blob or not tokens:
        return 0
    lower = blob.lower()
    return sum(3 if t in lower else 0 for t in tokens)


def run_smart_search(
    query: str,
    *,
    theme: str = "",
    mode: str = "keyword",
    limit: int = 8,
) -> Dict[str, Any]:
    tokens = _tokens(query)
    if theme and theme not in tokens:
        tokens.append(theme.lower())

    script_hits: List[Dict[str, Any]] = []
    for item in _s_grade_catalog().get("scripts") or []:
        if not isinstance(item, dict) or not item.get("enabled", True):
            continue
        blob = " ".join(
            str(item.get(k) or "")
            for k in ("title", "genre", "style", "track", "platform", "grade", "id")
        )
        score = _score_text(blob, tokens)
        if score > 0 or (not tokens and item.get("grade") == "S"):
            script_hits.append(
                {
                    "type": "reference-script",
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "grade": item.get("grade"),
                    "genre": item.get("genre"),
                    "platform": item.get("platform"),
                    "path": item.get("path"),
                    "score": score or (2 if item.get("grade") == "S" else 0),
                }
            )

    theme_hits: List[Dict[str, Any]] = []
    for code, tmpl in _theme_templates().items():
        if not isinstance(tmpl, dict):
            continue
        blob = " ".join(
            str(tmpl.get(k) or "")
            for k in ("displayName", "audienceFit", "coreConflictFormula", "structuralNotes")
        )
        blob += " " + " ".join(str(h) for h in (tmpl.get("sampleCoreHooks") or []))
        score = _score_text(blob, tokens)
        if score > 0:
            theme_hits.append(
                {
                    "type": "theme-template",
                    "themeCode": code,
                    "displayName": tmpl.get("displayName"),
                    "score": score,
                    "sampleHook": (tmpl.get("sampleCoreHooks") or [""])[0][:120],
                }
            )

    script_hits.sort(key=lambda x: (-int(x.get("score") or 0), x.get("title") or ""))
    theme_hits.sort(key=lambda x: (-int(x.get("score") or 0), x.get("themeCode") or ""))

    results = script_hits[:limit] + theme_hits[: max(2, limit // 2)]
    results.sort(key=lambda x: -int(x.get("score") or 0))

    return {
        "query": query,
        "mode": mode or "keyword",
        "resultCount": len(results),
        "results": results[:limit],
        "source": "smart-search-rule",
    }
