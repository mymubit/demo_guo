# -*- coding: utf-8 -*-
"""theme-recommender：题材推荐（规则层，读取 ThemeTemplate DB + 行业趋势）。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from apps.skill.config.portal.theme_templates import ThemeTemplateCatalogService

from .industry_benchmarks import load_industry_benchmarks


def _theme_templates() -> dict:
    return ThemeTemplateCatalogService.get_templates_map()


def _keyword_blob(brief: dict) -> str:
    parts = [
        brief.get("theme") or "",
        brief.get("themeDisplayName") or "",
        brief.get("coreHook") or "",
        brief.get("coreIdea") or "",
        brief.get("logline") or "",
    ]
    tf = brief.get("trendFormula") or {}
    if isinstance(tf, dict):
        parts.extend(
            [
                tf.get("coreConflictFormula") or "",
                tf.get("audienceFit") or "",
            ]
        )
    return " ".join(str(p) for p in parts if p).lower()


def _score_theme(theme_code: str, tmpl: dict, blob: str) -> int:
    score = 0
    display = str(tmpl.get("displayName") or "")
    for token in re.split(r"[\s、+/,，]+", display):
        t = token.strip().lower()
        if len(t) >= 2 and t in blob:
            score += 4
    formula = str(tmpl.get("coreConflictFormula") or "").lower()
    for token in re.split(r"[\s、+/,，]+", formula):
        t = token.strip()
        if len(t) >= 2 and t in blob:
            score += 2
    for hook in tmpl.get("sampleCoreHooks") or []:
        hook_l = str(hook).lower()
        if any(w in blob for w in ("复仇", "甜宠", "霸总", "重生", "穿越") if w in hook_l and w in blob):
            score += 3
        hook_tokens = [t for t in re.split(r"[\s、+/,，]+", hook_l) if len(t) >= 2]
        if sum(1 for t in hook_tokens if t in blob) >= 2:
            score += 4
    if theme_code.replace("-", "") in blob.replace("-", ""):
        score += 5
    return score


def recommend_themes(
    brief: Optional[dict] = None,
    *,
    limit: int = 5,
    current_theme: str = "",
) -> List[Dict[str, Any]]:
    brief = brief if isinstance(brief, dict) else {}
    blob = _keyword_blob(brief)
    current = (current_theme or brief.get("theme") or "").strip()

    ranked: List[Dict[str, Any]] = []
    for code, tmpl in _theme_templates().items():
        if not isinstance(tmpl, dict):
            continue
        score = _score_theme(code, tmpl, blob)
        ranked.append(
            {
                "themeCode": code,
                "displayName": tmpl.get("displayName") or code,
                "score": score,
                "audienceFit": (tmpl.get("audienceFit") or "")[:200],
                "recommendedEpisodes": tmpl.get("recommendedEpisodes"),
                "sampleHook": (tmpl.get("sampleCoreHooks") or [""])[0][:120],
                "matched": code == current,
            }
        )

    benchmarks = load_industry_benchmarks()
    trend = (benchmarks.get("themePopularityTrend") or {}).get("2026Forecast") or []
    for item in trend[:3]:
        label = str(item)
        for entry in ranked:
            if any(tok in label for tok in str(entry.get("displayName") or "").split("+")):
                entry["score"] = int(entry.get("score") or 0) + 2
                entry["trendTag"] = "2026Forecast"

    ranked.sort(key=lambda x: (-int(x.get("score") or 0), x.get("themeCode") or ""))
    if not blob.strip():
        ranked.sort(key=lambda x: (0 if x.get("themeCode") == "family-revenge" else 1))

    out = ranked[: max(1, int(limit or 5))]
    if current and not any(r.get("matched") for r in out):
        for entry in ranked:
            if entry.get("themeCode") == current:
                out = [entry] + [r for r in out if r.get("themeCode") != current][: limit - 1]
                break
    return out


def merge_theme_recommendations(brief: dict, *, limit: int = 5) -> dict:
    out = dict(brief or {})
    if out.get("themeRecommendations"):
        return out
    recs = recommend_themes(out, limit=limit)
    if recs:
        out["themeRecommendations"] = recs
    return out
