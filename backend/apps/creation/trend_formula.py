# -*- coding: utf-8 -*-
"""题材趋势 — C 端可读形态（不暴露 references 文件名）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from apps.skill.config.portal.creation_catalog import get_creation_catalog as _get_catalog
from apps.skill.config.portal.theme_templates import ThemeTemplateCatalogService


def _load_theme_entry(theme: str) -> Optional[dict]:
    return ThemeTemplateCatalogService.get_theme_entry(theme)


def _as_text_list(value: Any, *, limit: int = 6) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        rows: List[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                rows.append(item.strip())
            elif isinstance(item, dict):
                label = (
                    item.get("label")
                    or item.get("name")
                    or item.get("title")
                    or item.get("text")
                )
                if label:
                    rows.append(str(label).strip())
            if len(rows) >= limit:
                break
        return rows
    if isinstance(value, dict):
        rows = []
        for key, val in value.items():
            if isinstance(val, str) and val.strip():
                rows.append(f"{key}：{val.strip()}")
            elif len(rows) < limit:
                rows.append(str(key))
            if len(rows) >= limit:
                break
        return rows
    return []


_LEGACY_SAMPLE_HOOK_PREFIXES = ("参考钩子：", "题材示例开篇：")


def _strip_legacy_sample_hook_from_highlights(highlights: List[str]) -> List[str]:
    return [
        line
        for line in highlights
        if line and not any(str(line).startswith(prefix) for prefix in _LEGACY_SAMPLE_HOOK_PREFIXES)
    ]


def _extract_legacy_sample_hook(highlights: List[str]) -> Optional[str]:
    for line in highlights:
        text = str(line).strip()
        for prefix in _LEGACY_SAMPLE_HOOK_PREFIXES:
            if text.startswith(prefix):
                sample = text[len(prefix):].strip()
                if sample:
                    return sample[:120]
    return None


def apply_project_story_to_trend_formula(
    formula: Dict[str, Any],
    *,
    idea: str = "",
    opening_hooks: str = "",
    core_conflict: str = "",
) -> Dict[str, Any]:
    """将用户故事策划写入 trendFormula，并与题材库示例钩子分离展示。"""
    out = dict(formula)
    idea_text = (idea or "").strip()
    hooks_text = (opening_hooks or "").strip()
    conflict_text = (core_conflict or "").strip()

    highlights = list(out.get("highlights") or [])
    legacy_sample = _extract_legacy_sample_hook(highlights)
    if legacy_sample and not out.get("sampleHook"):
        out["sampleHook"] = legacy_sample
    highlights = _strip_legacy_sample_hook_from_highlights(highlights)

    if idea_text:
        out["projectIdea"] = idea_text[:800]
    if conflict_text:
        out["projectConflict"] = conflict_text[:800]
    if hooks_text:
        out["projectHook"] = hooks_text[:800]
    elif idea_text and not out.get("projectHook"):
        out["projectHook"] = idea_text[:400]

    if out.get("projectHook") or out.get("projectIdea"):
        out["highlights"] = highlights[:6]
    else:
        out["highlights"] = highlights[:6]

    return out


def trend_formula_has_internal_refs(trend: Optional[dict]) -> bool:
    if not isinstance(trend, dict):
        return False
    for item in trend.get("matchedTemplates") or []:
        if isinstance(item, dict) and (item.get("file") or item.get("excerpt")):
            return True
        if isinstance(item, str) and item.endswith(".json"):
            return True
    return False


def build_trend_formula(theme: str, *, theme_display_name: str = "") -> Dict[str, Any]:
    """从题材模板生成 C 端可读的 trendFormula。"""
    catalog = _get_catalog()
    display = (theme_display_name or catalog.theme_display_name(theme) or theme).strip()
    entry = _load_theme_entry(theme)

    formula: Dict[str, Any] = {
        "theme": theme,
        "themeDisplayName": display,
        "highlights": [],
        "matchedTemplates": [],
    }

    if not entry:
        return formula

    formula["audienceFit"] = (entry.get("audienceFit") or "").strip()
    formula["coreConflictFormula"] = (entry.get("coreConflictFormula") or "").strip()
    structural = (entry.get("structuralNotes") or "").strip()
    if structural:
        formula["structuralNotes"] = structural

    highlights: List[str] = []
    highlights.extend(_as_text_list(entry.get("keyReversalTypes"), limit=4))
    peaks = _as_text_list(entry.get("emotionalPeakMoments"), limit=2)
    if peaks:
        highlights.append(f"情绪高点：{'；'.join(peaks)}")
    hooks = _as_text_list(entry.get("sampleCoreHooks"), limit=1)
    if hooks:
        formula["sampleHook"] = hooks[0][:120]
    formula["highlights"] = highlights[:6]

    if entry.get("displayName") and entry["displayName"] != display:
        formula["themeDisplayName"] = str(entry["displayName"]).strip()

    return formula


def normalize_trend_formula(trend: Optional[dict], *, theme: str = "", theme_display_name: str = "") -> Dict[str, Any]:
    """将含 references 文件名的旧数据转为可读形态。"""
    if not isinstance(trend, dict):
        theme_key = (theme or "").strip()
        return build_trend_formula(theme_key, theme_display_name=theme_display_name) if theme_key else {}

    theme_key = (trend.get("theme") or theme or "").strip()
    display = (trend.get("themeDisplayName") or theme_display_name or "").strip()

    if trend_formula_has_internal_refs(trend) or not (trend.get("highlights") or trend.get("coreConflictFormula")):
        rebuilt = build_trend_formula(theme_key, theme_display_name=display)
        if rebuilt.get("theme") or rebuilt.get("themeDisplayName"):
            merged = {**rebuilt, **{k: v for k, v in trend.items() if k not in rebuilt and v}}
            merged["matchedTemplates"] = []
            return merged

    cleaned = dict(trend)
    highlights = list(cleaned.get("highlights") or [])
    legacy_sample = _extract_legacy_sample_hook(highlights)
    if legacy_sample and not cleaned.get("sampleHook"):
        cleaned["sampleHook"] = legacy_sample
    cleaned["highlights"] = _strip_legacy_sample_hook_from_highlights(highlights)
    cleaned["matchedTemplates"] = [
        item
        for item in (cleaned.get("matchedTemplates") or [])
        if isinstance(item, str) and item.strip() and not item.endswith(".json")
    ]
    return cleaned
