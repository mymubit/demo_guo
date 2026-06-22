# -*- coding: utf-8 -*-
"""Theme 原子子表 ↔ params cache 双向同步（skill-agent/13）。"""
from __future__ import annotations

from typing import Any, Dict

from apps.skill.models import ThemeTemplate


def sync_params_from_atomic_tables(theme: ThemeTemplate) -> Dict[str, Any]:
    """从子表聚合写回 params cache。"""
    from apps.skill.models_catalog import (
        ThemeActRatio,
        ThemeCharacterArchetype,
        ThemeEmotionCurve,
        ThemeEmotionalPeakMoment,
        ThemeHookType,
        ThemeReversalDensity,
    )

    params = dict(theme.params or {})
    params["act_ratio"] = [
        {"act": r.act_name, "ratio": r.ratio_percent}
        for r in ThemeActRatio.objects.filter(theme=theme, is_active=True).order_by("sort_order")
    ]
    params["emotion_curve"] = [
        {
            "from": r.episode_from,
            "to": r.episode_to,
            "value": r.emotion_value,
            "label": r.label,
        }
        for r in ThemeEmotionCurve.objects.filter(theme=theme, is_active=True).order_by("sort_order")
    ]
    params["hook_types"] = [
        {"type": r.hook_type, "description": r.description}
        for r in ThemeHookType.objects.filter(theme=theme, is_active=True).order_by("sort_order")
    ]
    params["character_archetypes"] = [
        {"name": r.name, "description": r.description, "fit_genres": r.fit_genres}
        for r in ThemeCharacterArchetype.objects.filter(theme=theme, is_active=True).order_by("sort_order")
    ]
    params["emotional_peaks"] = [
        {"episode": r.episode_hint, "moment": r.moment}
        for r in ThemeEmotionalPeakMoment.objects.filter(theme=theme, is_active=True).order_by("sort_order")
    ]
    params["reversal_density"] = [
        {"stage": r.stage, "density": r.density}
        for r in ThemeReversalDensity.objects.filter(theme=theme, is_active=True).order_by("sort_order")
    ]
    if getattr(theme, "description", ""):
        params["description"] = theme.description
    if getattr(theme, "core_conflict_formula", ""):
        params["core_conflict_formula"] = theme.core_conflict_formula
    if getattr(theme, "audience_fit", ""):
        params["audience_fit"] = theme.audience_fit
    if getattr(theme, "recommended_episodes", None):
        params["recommended_episodes"] = theme.recommended_episodes
    theme.params = params
    theme.save(update_fields=["params", "updated_at"])
    return params


def import_from_params(theme: ThemeTemplate, *, overwrite: bool = False) -> int:
    """params JSON → 原子子表（Phase B 导入）。"""
    from apps.skill.models_catalog import (
        ThemeActRatio,
        ThemeCharacterArchetype,
        ThemeEmotionCurve,
        ThemeEmotionalPeakMoment,
        ThemeHookType,
        ThemeReversalDensity,
    )

    params = dict(theme.params or {})
    if overwrite:
        ThemeActRatio.objects.filter(theme=theme).delete()
        ThemeEmotionCurve.objects.filter(theme=theme).delete()
        ThemeHookType.objects.filter(theme=theme).delete()
        ThemeCharacterArchetype.objects.filter(theme=theme).delete()
        ThemeEmotionalPeakMoment.objects.filter(theme=theme).delete()
        ThemeReversalDensity.objects.filter(theme=theme).delete()

    created = 0
    for idx, item in enumerate(params.get("act_ratio") or []):
        if not isinstance(item, dict):
            continue
        _, is_new = ThemeActRatio.objects.update_or_create(
            theme=theme,
            act_name=str(item.get("act") or f"act-{idx + 1}"),
            defaults={"ratio_percent": int(item.get("ratio") or 0), "sort_order": idx, "is_active": True},
        )
        if is_new:
            created += 1

    for idx, item in enumerate(params.get("emotion_curve") or []):
        if not isinstance(item, dict):
            continue
        _, is_new = ThemeEmotionCurve.objects.update_or_create(
            theme=theme,
            episode_from=int(item.get("from") or 1),
            episode_to=int(item.get("to") or 1),
            defaults={
                "emotion_value": int(item.get("value") or 0),
                "label": str(item.get("label") or ""),
                "sort_order": idx,
                "is_active": True,
            },
        )
        if is_new:
            created += 1

    sync_params_from_atomic_tables(theme)
    return created
