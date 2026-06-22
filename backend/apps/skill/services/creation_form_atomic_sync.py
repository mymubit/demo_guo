# -*- coding: utf-8 -*-
"""CreationForm JSON ↔ 原子子表同步（skill-agent/13 §3）。"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.db import transaction

from apps.skill.models import CreationFormOverrideConfig

logger = logging.getLogger(__name__)

CONFIG_KEY = "default"


def has_atomic_data(config_key: str = CONFIG_KEY) -> bool:
    from apps.skill.models_creation_form import CreationPlatform

    return CreationPlatform.objects.filter(config_key=config_key, is_active=True).exists()


def build_overrides_from_atomic(config_key: str = CONFIG_KEY) -> Dict[str, Any]:
    from apps.skill.models_creation_form import (
        CreationBudgetLevel,
        CreationEntry,
        CreationEntryProfile,
        CreationPlatform,
        CreationThemeEntry,
        EpisodeSettingsConfig,
        FormatVariant,
    )

    if not has_atomic_data(config_key):
        return {}

    platforms = [
        {"key": row.item_key, "name": row.name, "description": row.description}
        for row in CreationPlatform.objects.filter(config_key=config_key, is_active=True).order_by("sort_order")
    ]
    budget_levels = [
        {"key": row.item_key, "name": row.name, "description": row.description}
        for row in CreationBudgetLevel.objects.filter(config_key=config_key, is_active=True).order_by("sort_order")
    ]
    creation_entries = [
        {"key": row.item_key, "name": row.name}
        for row in CreationEntry.objects.filter(config_key=config_key, is_active=True).order_by("sort_order")
    ]
    format_variants = [
        {
            "key": row.item_key,
            "schemaKey": row.schema_key,
            "name": row.name,
            "description": row.description,
            "sceneHeading": row.scene_heading or None,
            "dialogueMarker": row.dialogue_marker or None,
            "actionMarker": row.action_marker or None,
        }
        for row in FormatVariant.objects.filter(config_key=config_key, is_active=True).order_by("sort_order")
    ]
    themes = [
        {
            "key": row.theme_key,
            "displayName": row.display_name or row.theme_key,
            "recommendedEpisodes": row.recommended_episodes,
            "recommendedDuration": row.recommended_duration,
            "color": row.color,
            "icon": row.icon,
            "enabled": row.is_enabled,
        }
        for row in CreationThemeEntry.objects.filter(config_key=config_key, is_enabled=True).order_by("sort_order")
    ]
    profiles: Dict[str, Any] = {}
    for row in CreationEntryProfile.objects.filter(config_key=config_key, is_active=True):
        if isinstance(row.profile, dict):
            profiles[row.entry_key] = dict(row.profile)

    episode_settings: Dict[str, Any] = {}
    eps = EpisodeSettingsConfig.objects.filter(config_key=config_key).first()
    if eps:
        episode_settings = {
            "min": eps.min_episodes,
            "max": eps.max_episodes,
            "step": eps.step,
            "default": eps.default_episodes,
            "presets": list(eps.presets or []),
            "durationMinutes": eps.duration_minutes,
        }

    overrides: Dict[str, Any] = {
        "platforms": platforms,
        "budgetLevels": budget_levels,
        "creationEntries": creation_entries,
        "formatVariants": format_variants,
        "themes": themes,
    }
    if profiles:
        overrides["creationEntryProfiles"] = profiles
    if episode_settings:
        overrides["episodeSettings"] = episode_settings
    return overrides


@transaction.atomic
def sync_overrides_cache(config_key: str = CONFIG_KEY) -> bool:
    """原子表 → overrides JSON cache。"""
    built = build_overrides_from_atomic(config_key)
    if not built:
        return False
    row, _ = CreationFormOverrideConfig.objects.get_or_create(
        config_key=config_key,
        defaults={"overrides": {}, "episode_settings": {}},
    )
    merged = dict(row.overrides) if isinstance(row.overrides, dict) else {}
    merged.update(built)
    row.overrides = merged
    if built.get("episodeSettings"):
        row.episode_settings = dict(built["episodeSettings"])
    row.save(update_fields=["overrides", "episode_settings", "updated_at"])
    return True


@transaction.atomic
def migrate_from_overrides(*, config_key: str = CONFIG_KEY, overwrite: bool = False) -> Dict[str, int]:
    """overrides JSON → 原子子表。"""
    from apps.skill.models_creation_form import (
        CreationBudgetLevel,
        CreationEntry,
        CreationEntryProfile,
        CreationPlatform,
        CreationThemeEntry,
        EpisodeSettingsConfig,
        FormatVariant,
    )

    row = CreationFormOverrideConfig.objects.filter(config_key=config_key).first()
    if not row:
        return {"created": 0}

    overrides = dict(row.overrides or {})
    if overwrite:
        CreationPlatform.objects.filter(config_key=config_key).delete()
        CreationBudgetLevel.objects.filter(config_key=config_key).delete()
        CreationEntry.objects.filter(config_key=config_key).delete()
        CreationEntryProfile.objects.filter(config_key=config_key).delete()
        FormatVariant.objects.filter(config_key=config_key).delete()
        CreationThemeEntry.objects.filter(config_key=config_key).delete()
        EpisodeSettingsConfig.objects.filter(config_key=config_key).delete()

    created = 0

    def _upsert_platform(item: Dict[str, Any], idx: int) -> None:
        nonlocal created
        key = str(item.get("key") or "").strip()
        if not key:
            return
        _, is_new = CreationPlatform.objects.update_or_create(
            config_key=config_key,
            item_key=key,
            defaults={
                "name": str(item.get("name") or key),
                "description": str(item.get("description") or ""),
                "sort_order": idx,
                "is_active": True,
            },
        )
        if is_new:
            created += 1

    for idx, item in enumerate(overrides.get("platforms") or []):
        if isinstance(item, dict):
            _upsert_platform(item, idx)

    for idx, item in enumerate(overrides.get("budgetLevels") or []):
        if not isinstance(item, dict) or not item.get("key"):
            continue
        _, is_new = CreationBudgetLevel.objects.update_or_create(
            config_key=config_key,
            item_key=str(item["key"]),
            defaults={
                "name": str(item.get("name") or item["key"]),
                "description": str(item.get("description") or ""),
                "sort_order": idx,
                "is_active": True,
            },
        )
        if is_new:
            created += 1

    for idx, item in enumerate(overrides.get("creationEntries") or []):
        if not isinstance(item, dict) or not item.get("key"):
            continue
        _, is_new = CreationEntry.objects.update_or_create(
            config_key=config_key,
            item_key=str(item["key"]),
            defaults={
                "name": str(item.get("name") or item["key"]),
                "sort_order": idx,
                "is_active": True,
            },
        )
        if is_new:
            created += 1

    profiles = overrides.get("creationEntryProfiles") or {}
    if isinstance(profiles, dict):
        for entry_key, profile in profiles.items():
            if not isinstance(profile, dict):
                continue
            _, is_new = CreationEntryProfile.objects.update_or_create(
                config_key=config_key,
                entry_key=str(entry_key),
                defaults={"profile": profile, "is_active": True},
            )
            if is_new:
                created += 1

    for idx, item in enumerate(overrides.get("formatVariants") or []):
        if not isinstance(item, dict) or not item.get("key"):
            continue
        _, is_new = FormatVariant.objects.update_or_create(
            config_key=config_key,
            item_key=str(item["key"]),
            defaults={
                "schema_key": str(item.get("schemaKey") or ""),
                "name": str(item.get("name") or item["key"]),
                "description": str(item.get("description") or ""),
                "scene_heading": str(item.get("sceneHeading") or ""),
                "dialogue_marker": str(item.get("dialogueMarker") or ""),
                "action_marker": str(item.get("actionMarker") or ""),
                "sort_order": idx,
                "is_active": True,
            },
        )
        if is_new:
            created += 1

    for idx, item in enumerate(overrides.get("themes") or []):
        if not isinstance(item, dict) or not item.get("key"):
            continue
        _, is_new = CreationThemeEntry.objects.update_or_create(
            config_key=config_key,
            theme_key=str(item["key"]),
            defaults={
                "display_name": str(item.get("displayName") or item["key"]),
                "recommended_episodes": item.get("recommendedEpisodes"),
                "recommended_duration": item.get("recommendedDuration"),
                "color": str(item.get("color") or "#667eea"),
                "icon": str(item.get("icon") or "🎬"),
                "is_enabled": bool(item.get("enabled", True)),
                "sort_order": idx,
            },
        )
        if is_new:
            created += 1

    eps = overrides.get("episodeSettings") or row.episode_settings or {}
    if isinstance(eps, dict) and eps:
        _, is_new = EpisodeSettingsConfig.objects.update_or_create(
            config_key=config_key,
            defaults={
                "min_episodes": int(eps.get("min") or 20),
                "max_episodes": int(eps.get("max") or 200),
                "step": int(eps.get("step") or 10),
                "default_episodes": int(eps.get("default") or 80),
                "presets": list(eps.get("presets") or []),
                "duration_minutes": int(eps.get("durationMinutes") or 2),
            },
        )
        if is_new:
            created += 1

    sync_overrides_cache(config_key)
    return {"created": created}
