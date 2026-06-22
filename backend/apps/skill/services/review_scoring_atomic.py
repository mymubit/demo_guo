# -*- coding: utf-8 -*-
"""ReviewScoring 原子预设 ↔ legacy blob 双读（skill-agent/13 §4）。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from apps.agent.models import ReviewGradeThreshold, ReviewScoringDimension, ReviewScoringPreset
from apps.skill.config.portal.review_scoring_defaults import REVIEW_SCORING_PRESETS


def seed_presets_from_defaults(*, overwrite: bool = False) -> int:
    created = 0
    for preset_id, preset in REVIEW_SCORING_PRESETS.items():
        row, is_new = ReviewScoringPreset.objects.update_or_create(
            preset_id=preset_id,
            defaults={
                "name": str(preset.get("label") or preset_id),
                "is_active": preset_id == "standard",
                "pass_threshold": int(preset.get("pass_threshold") or 70),
                "min_sub_item_score": 75,
            },
        )
        if is_new:
            created += 1
        if overwrite:
            ReviewScoringDimension.objects.filter(preset=row).delete()
            ReviewGradeThreshold.objects.filter(preset=row).delete()
        weights = preset.get("weights") or {}
        for idx, (dim_key, weight) in enumerate(weights.items()):
            ReviewScoringDimension.objects.update_or_create(
                preset=row,
                dimension_key=str(dim_key),
                defaults={"weight": weight, "sort_order": idx},
            )
        grades = preset.get("grade_thresholds") or {}
        for idx, (grade, min_score) in enumerate(grades.items()):
            ReviewGradeThreshold.objects.update_or_create(
                preset=row,
                grade=str(grade),
                defaults={"min_score": int(min_score), "sort_order": idx},
            )
    return created


def resolve_active_preset() -> Optional[ReviewScoringPreset]:
    return ReviewScoringPreset.objects.filter(is_active=True).order_by("-updated_at").first()


def expand_preset(preset: ReviewScoringPreset) -> Dict[str, Any]:
    weights: Dict[str, int] = {}
    for row in ReviewScoringDimension.objects.filter(preset=preset).order_by("sort_order"):
        weights[row.dimension_key] = int(row.weight)
    grade_thresholds: Dict[str, int] = {}
    for row in ReviewGradeThreshold.objects.filter(preset=preset).order_by("sort_order"):
        grade_thresholds[row.grade] = int(row.min_score)
    return {
        "preset_id": preset.preset_id,
        "weights": weights,
        "grade_thresholds": grade_thresholds,
        "pass_threshold": int(preset.pass_threshold),
        "min_sub_item_score": int(preset.min_sub_item_score),
        "release_pass_score": int(preset.pass_threshold),
    }
