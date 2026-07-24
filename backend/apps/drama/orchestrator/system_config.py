# -*- coding: utf-8 -*-
"""V3 系统配置：foundation presets ⊕ overlay 修订。"""
from __future__ import annotations

import logging
from typing import Any

from django.db import transaction

from apps.core.exceptions import VALIDATION_ERROR, BusinessException
from apps.drama.models import V3SystemConfigRevision
from apps.drama.services.skills_loader import get_skills_loader

logger = logging.getLogger(__name__)

ALLOWED_OVERLAY_KEYS = frozenset(
    {
        "target_platform",
        "scoring_preset",
        "quality_pass_threshold",
        "daily_cost_alert_cny",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {"generic", "douyin", "kuaishou", "wechat_miniprogram"}
)
ALLOWED_SCORING_PRESETS = frozenset(
    {"standard", "strict", "relaxed", "rhythm_first"}
)

DEFAULT_TARGET_PLATFORM = "generic"
DEFAULT_SCORING_PRESET = "standard"
DEFAULT_PASS_THRESHOLD = 75.0


def resolve_system_config() -> dict[str, Any]:
    """返回 {revision, overlay, effective}；无修订时 revision=0, overlay={}. """
    latest = V3SystemConfigRevision.objects.order_by("-revision").first()
    if latest is None:
        overlay: dict[str, Any] = {}
        revision = 0
    else:
        overlay = dict(latest.overlay or {})
        revision = int(latest.revision)
    return {
        "revision": revision,
        "overlay": overlay,
        "effective": _build_effective(overlay),
    }


@transaction.atomic
def save_system_overlay(
    *,
    overlay: dict,
    actor: str,
    change_reason: str = "",
) -> dict[str, Any]:
    """校验允许键 → 与上一 revision merge → 新 revision → 返回 resolve 结果。

    合并语义：请求中出现的键覆盖旧值；未出现的键保留。
    ``quality_pass_threshold`` / ``daily_cost_alert_cny`` 传 null 表示显式清除。
    """
    if not isinstance(overlay, dict):
        raise BusinessException(
            VALIDATION_ERROR,
            "overlay 必须为对象",
            http_status=400,
        )
    patch, clear_keys = _sanitize_overlay_patch(overlay)
    latest = (
        V3SystemConfigRevision.objects.select_for_update()
        .order_by("-revision")
        .first()
    )
    previous = dict(latest.overlay or {}) if latest else {}
    merged = {**previous, **patch}
    for key in clear_keys:
        merged.pop(key, None)
    next_revision = (latest.revision + 1) if latest else 1
    V3SystemConfigRevision.objects.create(
        revision=next_revision,
        overlay=merged,
        updated_by=str(actor or ""),
        change_reason=str(change_reason or "")[:500],
    )
    return resolve_system_config()


def _sanitize_overlay_patch(
    raw: dict[str, Any],
) -> tuple[dict[str, Any], set[str]]:
    """返回 (覆盖补丁, 需显式清除的键集合)。"""
    unknown = sorted(set(raw.keys()) - ALLOWED_OVERLAY_KEYS)
    if unknown:
        logger.warning("system config overlay 忽略未知键: %s", unknown)

    patch: dict[str, Any] = {}
    clear_keys: set[str] = set()

    if "target_platform" in raw:
        platform = raw["target_platform"]
        if platform not in ALLOWED_PLATFORMS:
            raise BusinessException(
                VALIDATION_ERROR,
                f"非法 target_platform: {platform}",
                http_status=400,
            )
        patch["target_platform"] = platform

    if "scoring_preset" in raw:
        preset = raw["scoring_preset"]
        if preset not in ALLOWED_SCORING_PRESETS:
            raise BusinessException(
                VALIDATION_ERROR,
                f"非法 scoring_preset: {preset}",
                http_status=400,
            )
        patch["scoring_preset"] = preset

    if "quality_pass_threshold" in raw:
        value = raw["quality_pass_threshold"]
        if value is None:
            clear_keys.add("quality_pass_threshold")
        else:
            patch["quality_pass_threshold"] = _coerce_threshold(value)

    if "daily_cost_alert_cny" in raw:
        value = raw["daily_cost_alert_cny"]
        if value is None:
            clear_keys.add("daily_cost_alert_cny")
        else:
            patch["daily_cost_alert_cny"] = _coerce_non_negative(
                value,
                field="daily_cost_alert_cny",
            )
    return patch, clear_keys


def _coerce_threshold(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BusinessException(
            VALIDATION_ERROR,
            "quality_pass_threshold 必须为 0–100 数值",
            http_status=400,
        )
    threshold = float(value)
    if threshold < 0 or threshold > 100:
        raise BusinessException(
            VALIDATION_ERROR,
            "quality_pass_threshold 必须为 0–100 数值",
            http_status=400,
        )
    return threshold


def _coerce_non_negative(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BusinessException(
            VALIDATION_ERROR,
            f"{field} 必须为 >= 0 的数值",
            http_status=400,
        )
    number = float(value)
    if number < 0:
        raise BusinessException(
            VALIDATION_ERROR,
            f"{field} 必须为 >= 0 的数值",
            http_status=400,
        )
    return number


def _build_effective(overlay: dict[str, Any]) -> dict[str, Any]:
    loader = get_skills_loader()
    scoring_doc = loader.load_seed_yaml("foundation/presets/scoring-presets.yaml")
    platform_doc = loader.load_seed_yaml("foundation/presets/platform-profiles.yaml")

    presets = scoring_doc.get("presets") or {}
    recommendations = scoring_doc.get("platform_recommendations") or {}
    platforms = platform_doc.get("platforms") or {}

    target_platform = overlay.get("target_platform") or DEFAULT_TARGET_PLATFORM
    if target_platform not in ALLOWED_PLATFORMS:
        target_platform = DEFAULT_TARGET_PLATFORM

    if "scoring_preset" in overlay:
        scoring_preset = overlay["scoring_preset"]
    else:
        scoring_preset = recommendations.get(target_platform) or DEFAULT_SCORING_PRESET
    if scoring_preset not in ALLOWED_SCORING_PRESETS:
        scoring_preset = DEFAULT_SCORING_PRESET

    preset_meta = presets.get(scoring_preset) or presets.get(DEFAULT_SCORING_PRESET) or {}
    if "quality_pass_threshold" in overlay:
        pass_threshold = float(overlay["quality_pass_threshold"])
    else:
        raw_threshold = preset_meta.get("pass_threshold", DEFAULT_PASS_THRESHOLD)
        pass_threshold = float(raw_threshold)

    platform_meta = platforms.get(target_platform) or platforms.get(DEFAULT_TARGET_PLATFORM) or {}
    platform_label_zh = str(platform_meta.get("label_zh") or target_platform)

    raw_alert = overlay.get("daily_cost_alert_cny")
    daily_cost_alert_cny = (
        float(raw_alert) if raw_alert is not None else None
    )

    return {
        "target_platform": target_platform,
        "scoring_preset": scoring_preset,
        "pass_threshold": pass_threshold,
        "platform_label_zh": platform_label_zh,
        "daily_cost_alert_cny": daily_cost_alert_cny,
    }
