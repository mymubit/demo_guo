# -*- coding: utf-8 -*-
"""质量审查评分 — DB SSOT，代码默认值兜底。"""
from __future__ import annotations

from typing import Any, Dict

from apps.agent.models import ReviewScoringConfig
from .review_scoring_defaults import (
    DEFAULT_GRADE_THRESHOLDS,
    DEFAULT_MIN_SUB_ITEM_SCORE,
    DEFAULT_PASS_THRESHOLD,
    DEFAULT_RELEASE_PASS_SCORE,
    DEFAULT_REVIEW_WEIGHTS,
    REVIEW_SCORING_PRESETS,
    detect_review_scoring_preset,
    expand_review_scoring_preset,
    list_review_scoring_presets,
)

CONFIG_KEY = "default"


class ReviewScoringService:
    @staticmethod
    def resolve() -> Dict[str, Any]:
        row = None
        try:
            row = ReviewScoringConfig.objects.filter(config_key=CONFIG_KEY).first()
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ != "DatabaseOperationForbidden":
                raise
        weights = dict(DEFAULT_REVIEW_WEIGHTS)
        grade_thresholds = dict(DEFAULT_GRADE_THRESHOLDS)
        pass_threshold = DEFAULT_PASS_THRESHOLD
        min_sub_item_score = DEFAULT_MIN_SUB_ITEM_SCORE

        if row:
            if isinstance(row.weights, dict) and row.weights:
                weights.update({k: int(v) for k, v in row.weights.items() if k in weights})
            if isinstance(row.grade_thresholds, dict) and row.grade_thresholds:
                grade_thresholds.update(
                    {k: int(v) for k, v in row.grade_thresholds.items() if k in grade_thresholds}
                )
            pass_threshold = int(row.pass_threshold or DEFAULT_PASS_THRESHOLD)
            min_sub_item_score = int(
                getattr(row, "min_sub_item_score", None) or DEFAULT_MIN_SUB_ITEM_SCORE
            )

        release_pass_score = pass_threshold
        return {
            "weights": weights,
            "grade_thresholds": grade_thresholds,
            "pass_threshold": pass_threshold,
            "release_pass_score": release_pass_score,
            "min_sub_item_score": min_sub_item_score,
        }

    @staticmethod
    def get_admin_payload() -> Dict[str, Any]:
        cfg = ReviewScoringService.resolve()
        row = ReviewScoringConfig.objects.filter(config_key=CONFIG_KEY).first()
        preset_id = detect_review_scoring_preset(cfg)
        return {
            "id": str(row.id) if row else None,
            "preset_id": preset_id,
            "presets": list_review_scoring_presets(),
            "weights": cfg["weights"],
            "grade_thresholds": cfg["grade_thresholds"],
            "pass_threshold": cfg["pass_threshold"],
            "min_sub_item_score": cfg["min_sub_item_score"],
            "source": "db" if row else "default",
            "updated_at": row.updated_at if row else None,
        }

    @staticmethod
    def save(data: Dict[str, Any]) -> ReviewScoringConfig:
        payload = dict(data or {})
        preset_id = str(payload.get("preset_id") or "").strip()
        if preset_id and preset_id != "custom" and preset_id in REVIEW_SCORING_PRESETS:
            payload.update(expand_review_scoring_preset(preset_id))

        row, _ = ReviewScoringConfig.objects.get_or_create(
            config_key=CONFIG_KEY,
            defaults={
                "weights": dict(DEFAULT_REVIEW_WEIGHTS),
                "grade_thresholds": dict(DEFAULT_GRADE_THRESHOLDS),
                "pass_threshold": DEFAULT_PASS_THRESHOLD,
                "min_sub_item_score": DEFAULT_MIN_SUB_ITEM_SCORE,
            },
        )
        if "weights" in payload and isinstance(payload["weights"], dict):
            row.weights = {k: int(v) for k, v in payload["weights"].items()}
        if "grade_thresholds" in payload and isinstance(payload["grade_thresholds"], dict):
            row.grade_thresholds = {k: int(v) for k, v in payload["grade_thresholds"].items()}
        if "pass_threshold" in payload:
            row.pass_threshold = max(0, min(100, int(payload["pass_threshold"])))
        if "min_sub_item_score" in payload:
            row.min_sub_item_score = max(0, min(100, int(payload["min_sub_item_score"])))
        row.save()
        return row

    @staticmethod
    def seed_defaults() -> bool:
        row, created = ReviewScoringConfig.objects.get_or_create(
            config_key=CONFIG_KEY,
            defaults={
                "weights": dict(DEFAULT_REVIEW_WEIGHTS),
                "grade_thresholds": dict(DEFAULT_GRADE_THRESHOLDS),
                "pass_threshold": DEFAULT_PASS_THRESHOLD,
                "min_sub_item_score": DEFAULT_MIN_SUB_ITEM_SCORE,
            },
        )
        return created

    @classmethod
    def import_thresholds_from_disk(cls) -> bool:
        """从 skill-thresholds.json seed 放行线与子项最低分（仅首次或空值）。"""
        try:
            from apps.workflow.fusion.config_loader import get_fusion_config

            thresholds = get_fusion_config().skill_thresholds.get("thresholds") or {}
        except Exception:  # noqa: BLE001
            return False

        row, created = ReviewScoringConfig.objects.get_or_create(
            config_key=CONFIG_KEY,
            defaults={
                "weights": dict(DEFAULT_REVIEW_WEIGHTS),
                "grade_thresholds": dict(DEFAULT_GRADE_THRESHOLDS),
                "pass_threshold": int(thresholds.get("releasePassScore") or DEFAULT_RELEASE_PASS_SCORE),
                "min_sub_item_score": int(thresholds.get("minSubItemScore") or DEFAULT_MIN_SUB_ITEM_SCORE),
            },
        )
        updated = False
        if created:
            return True
        if row.pass_threshold == DEFAULT_PASS_THRESHOLD and thresholds.get("releasePassScore"):
            row.pass_threshold = int(thresholds["releasePassScore"])
            updated = True
        if getattr(row, "min_sub_item_score", DEFAULT_MIN_SUB_ITEM_SCORE) == DEFAULT_MIN_SUB_ITEM_SCORE:
            if thresholds.get("minSubItemScore"):
                row.min_sub_item_score = int(thresholds["minSubItemScore"])
                updated = True
        if updated:
            row.save(update_fields=["pass_threshold", "min_sub_item_score", "updated_at"])
        return updated or created
