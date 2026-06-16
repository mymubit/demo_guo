# -*- coding: utf-8 -*-
"""创作表单 Catalog — DB SSOT；磁盘 project-config 仅 import/sync 引导。"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .creation_form_profiles import DEFAULT_CREATION_ENTRY_PROFILES
from .creation_form_defaults import (
    CREATION_ENTRY_LABEL_FALLBACK,
    DEFAULT_BUDGET_LEVELS,
    DEFAULT_CREATION_ENTRIES,
    DEFAULT_EPISODE_SETTINGS,
    DEFAULT_FORMAT_VARIANTS,
    DEFAULT_FORMAT_VARIANT_SCHEMA,
    DEFAULT_PLATFORMS,
    LETTER_FROM_VARIANT,
    VARIANT_LETTER_MAP,
)
from apps.skill.models import CreationFormOverrideConfig

logger = logging.getLogger(__name__)

CONFIG_KEY = "default"


class CreationFormOverrideService:
    @staticmethod
    def _get_row() -> CreationFormOverrideConfig:
        row, _ = CreationFormOverrideConfig.objects.get_or_create(
            config_key=CONFIG_KEY,
            defaults={"overrides": {}, "episode_settings": {}},
        )
        return row

    @staticmethod
    def _clear_catalog_cache() -> None:
        try:
            from apps.workflow.fusion.ssot_catalog import get_ssot_catalog

            get_ssot_catalog.cache_clear()
        except Exception as exc:  # noqa: BLE001
            logger.debug("ssot catalog cache clear failed: %s", exc)

    @staticmethod
    def get_overrides() -> Dict[str, Any]:
        try:
            row = CreationFormOverrideService._get_row()
            if isinstance(row.overrides, dict):
                return row.overrides
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ != "DatabaseOperationForbidden":
                logger.debug("creation form overrides DB 读取失败: %s", exc)
        return {}

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(base or {})
        for key, val in (override or {}).items():
            if isinstance(val, dict) and isinstance(out.get(key), dict):
                out[key] = CreationFormOverrideService._deep_merge(out[key], val)
            else:
                out[key] = val
        return out

    @staticmethod
    def _schema_enum(*path: str) -> List[str]:
        from apps.workflow.pipeline_store import FusionPipelineDbService

        schema = FusionPipelineDbService.get_schema_dict("project-brief.schema.json") or {}
        cur: Any = schema
        for key in path:
            cur = (cur.get("properties") or {}).get(key) or {}
        enums = cur.get("enum") if isinstance(cur, dict) else None
        return list(enums) if enums else []

    @staticmethod
    def _load_disk_project_meta() -> Dict[str, Any]:
        try:
            from apps.workflow.fusion.config_loader import get_fusion_config

            meta = get_fusion_config().project_config.get("projectMeta", {}) or {}
            return meta if isinstance(meta, dict) else {}
        except Exception as exc:  # noqa: BLE001
            logger.debug("disk projectMeta 读取失败: %s", exc)
            return {}

    @staticmethod
    def _load_disk_creation_form() -> Dict[str, Any]:
        meta = CreationFormOverrideService._load_disk_project_meta()
        creation_form = meta.get("creationForm") or {}
        return creation_form if isinstance(creation_form, dict) else {}

    @staticmethod
    def _load_disk_format_variants() -> Dict[str, Any]:
        try:
            from apps.workflow.fusion.config_loader import get_fusion_config

            variants = get_fusion_config().project_config.get("formatVariants") or {}
            return variants if isinstance(variants, dict) else {}
        except Exception as exc:  # noqa: BLE001
            logger.debug("disk formatVariants 读取失败: %s", exc)
            return {}

    @staticmethod
    def _load_disk_theme_templates() -> Dict[str, Any]:
        try:
            from apps.workflow.fusion.config_loader import get_fusion_config

            path = get_fusion_config().root / "references" / "theme-templates.json"
            if not path.is_file():
                return {}
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            templates = data.get("themeTemplates") or {}
            return templates if isinstance(templates, dict) else {}
        except Exception as exc:  # noqa: BLE001
            logger.debug("disk theme-templates 读取失败: %s", exc)
            return {}

    @classmethod
    def _merge_seed_and_disk_profiles(cls) -> Dict[str, Any]:
        profiles = {key: dict(value) for key, value in DEFAULT_CREATION_ENTRY_PROFILES.items()}
        disk = cls._load_disk_creation_form().get("creationEntryProfiles") or {}
        if isinstance(disk, dict):
            for key, value in disk.items():
                if not isinstance(value, dict):
                    continue
                base = profiles.get(key, DEFAULT_CREATION_ENTRY_PROFILES.get("from-scratch", {}))
                profiles[key] = cls._deep_merge(base, value)
        return profiles

    @classmethod
    def _build_disk_catalog(cls) -> Dict[str, Any]:
        meta = cls._load_disk_project_meta()
        creation_form = cls._load_disk_creation_form()
        format_variants_raw = cls._load_disk_format_variants()
        theme_templates = cls._load_disk_theme_templates()

        platform_keys = list(meta.get("platforms") or cls._schema_enum("targetPlatform") or ["douyin"])
        platform_labels = meta.get("platformLabels") or {}
        platform_hints = creation_form.get("platformHints") or {}
        platforms = [
            {
                "key": p,
                "name": platform_labels.get(p, p),
                "description": platform_hints.get(p, ""),
            }
            for p in platform_keys
        ] or list(DEFAULT_PLATFORMS)

        budget_labels = meta.get("budgetLevelLabels") or {}
        budget_hints = creation_form.get("budgetLevelHints") or {}
        budget_keys = cls._schema_enum("budgetLevel") or ["low", "medium", "high"]
        budget_levels = [
            {
                "key": k,
                "name": budget_labels.get(k, k),
                "description": budget_hints.get(k, ""),
            }
            for k in budget_keys
        ] or list(DEFAULT_BUDGET_LEVELS)

        entry_labels = meta.get("creationEntryLabels") or {}
        entry_keys = cls._schema_enum("creationEntry") or [e["key"] for e in DEFAULT_CREATION_ENTRIES]
        creation_entries = [
            {
                "key": k,
                "name": entry_labels.get(k) or CREATION_ENTRY_LABEL_FALLBACK.get(k, k),
            }
            for k in entry_keys
        ] or list(DEFAULT_CREATION_ENTRIES)

        format_variants: List[Dict[str, Any]] = []
        for schema_key, letter in VARIANT_LETTER_MAP.items():
            block = format_variants_raw.get(schema_key)
            if not block or schema_key == "default":
                continue
            format_variants.append(
                {
                    "key": letter,
                    "schemaKey": schema_key,
                    "name": block.get("name", schema_key),
                    "description": block.get("description", ""),
                    "sceneHeading": block.get("sceneHeading"),
                    "dialogueMarker": block.get("dialogueMarker"),
                    "actionMarker": block.get("actionMarker"),
                }
            )
        if not format_variants:
            format_variants = list(DEFAULT_FORMAT_VARIANTS)

        supported_themes = list(meta.get("supportedThemes") or [])
        themes: List[Dict[str, Any]] = []
        for key in supported_themes:
            tpl = theme_templates.get(key) or {}
            themes.append(
                {
                    "key": key,
                    "displayName": tpl.get("displayName") or key,
                    "recommendedEpisodes": tpl.get("recommendedEpisodes"),
                    "recommendedDuration": tpl.get("recommendedDuration"),
                    "color": tpl.get("color") or "#667eea",
                    "icon": tpl.get("icon") or tpl.get("emoji") or "🎬",
                    "enabled": tpl.get("enabled", True),
                }
            )

        return {
            "platforms": platforms,
            "budgetLevels": budget_levels,
            "creationEntries": creation_entries,
            "formatVariants": format_variants,
            "themes": themes,
            "sections": dict(creation_form.get("sections") or {}),
            "episodeSettings": dict(creation_form.get("episodeSettings") or DEFAULT_EPISODE_SETTINGS),
            "creationEntryProfiles": cls._merge_seed_and_disk_profiles(),
            "defaultFormatVariant": str(
                format_variants_raw.get("default") or DEFAULT_FORMAT_VARIANT_SCHEMA
            ),
        }

    @classmethod
    def import_catalog_from_disk(cls, *, overwrite: bool = False) -> bool:
        disk_catalog = cls._build_disk_catalog()
        if not disk_catalog.get("platforms"):
            logger.warning("[CreationForm] import_catalog_from_disk: 磁盘 catalog 为空")
            return False

        row = cls._get_row()
        overrides = dict(row.overrides) if isinstance(row.overrides, dict) else {}
        if overrides.get("platforms") and not overwrite:
            return False

        for key, value in disk_catalog.items():
            overrides[key] = value
        row.overrides = overrides
        row.save(update_fields=["overrides", "updated_at"])
        cls._clear_catalog_cache()
        return True

    @classmethod
    def sync_catalog_from_disk(cls) -> bool:
        disk_catalog = cls._build_disk_catalog()
        if not disk_catalog.get("platforms"):
            return False

        row = cls._get_row()
        overrides = dict(row.overrides) if isinstance(row.overrides, dict) else {}

        if disk_catalog.get("creationEntryProfiles"):
            existing = overrides.get("creationEntryProfiles")
            seed_disk = disk_catalog["creationEntryProfiles"]
            if isinstance(existing, dict) and existing:
                merged = {key: dict(value) for key, value in existing.items()}
                for key, value in seed_disk.items():
                    base = merged.get(key, DEFAULT_CREATION_ENTRY_PROFILES.get("from-scratch", {}))
                    merged[key] = cls._deep_merge(base, value)
                overrides["creationEntryProfiles"] = merged
            else:
                overrides["creationEntryProfiles"] = seed_disk

        for key in ("platforms", "budgetLevels", "creationEntries", "formatVariants", "themes"):
            disk_val = disk_catalog.get(key)
            if not disk_val:
                continue
            if key == "themes" and not disk_val:
                continue
            if isinstance(disk_val, list):
                by_key = {item.get("key"): dict(item) for item in overrides.get(key) or [] if item.get("key")}
                for item in disk_val:
                    item_key = item.get("key")
                    if item_key and item_key in by_key:
                        by_key[item_key] = cls._deep_merge(by_key[item_key], item)
                    elif item_key:
                        by_key[item_key] = dict(item)
                overrides[key] = list(by_key.values()) if by_key else list(disk_val)
            else:
                overrides[key] = disk_val

        if disk_catalog.get("sections"):
            overrides["sections"] = cls._deep_merge(
                overrides.get("sections") or {},
                disk_catalog["sections"],
            )
        if disk_catalog.get("episodeSettings"):
            overrides["episodeSettings"] = cls._deep_merge(
                overrides.get("episodeSettings") or {},
                disk_catalog["episodeSettings"],
            )
        if disk_catalog.get("defaultFormatVariant"):
            overrides["defaultFormatVariant"] = disk_catalog["defaultFormatVariant"]

        row.overrides = overrides
        row.save(update_fields=["overrides", "updated_at"])
        cls._clear_catalog_cache()
        return True

    # 兼容旧 API 名称
    import_entry_profiles_from_disk = import_catalog_from_disk
    sync_entry_profiles_from_disk = sync_catalog_from_disk

    @classmethod
    def ensure_defaults(cls) -> bool:
        try:
            overrides = cls.get_overrides()
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ == "DatabaseOperationForbidden":
                return False
            logger.warning("[CreationForm] ensure_defaults skipped: %s", exc)
            return False

        if overrides.get("platforms"):
            return False

        try:
            return cls.import_catalog_from_disk(overwrite=False)
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ == "DatabaseOperationForbidden":
                return False
            logger.warning("[CreationForm] ensure_defaults failed: %s", exc)
            return False

    @staticmethod
    def _themes_from_db_templates() -> List[Dict[str, Any]]:
        try:
            from apps.skill.config.portal.skill_settings import ThemeTemplateService

            themes = []
            for row in ThemeTemplateService.list_themes(only_active=True):
                params = row.get("params") or {}
                themes.append(
                    {
                        "key": row.get("theme_code") or "",
                        "displayName": row.get("theme_name") or row.get("theme_code") or "",
                        "recommendedEpisodes": params.get("recommendedEpisodes"),
                        "recommendedDuration": params.get("recommendedDuration"),
                        "color": params.get("color") or "#667eea",
                        "icon": params.get("icon") or params.get("emoji") or "🎬",
                        "enabled": bool(row.get("is_active", True)),
                    }
                )
            return [t for t in themes if t.get("key")]
        except Exception as exc:  # noqa: BLE001
            logger.debug("ThemeTemplate DB 读取失败: %s", exc)
            return []

    @classmethod
    def get_platforms(cls) -> List[Dict[str, Any]]:
        cls.ensure_defaults()
        platforms = cls.get_overrides().get("platforms")
        return list(platforms) if isinstance(platforms, list) and platforms else list(DEFAULT_PLATFORMS)

    @classmethod
    def get_budget_levels(cls) -> List[Dict[str, str]]:
        cls.ensure_defaults()
        levels = cls.get_overrides().get("budgetLevels")
        return list(levels) if isinstance(levels, list) and levels else list(DEFAULT_BUDGET_LEVELS)

    @classmethod
    def get_creation_entries(cls) -> List[Dict[str, str]]:
        cls.ensure_defaults()
        entries = cls.get_overrides().get("creationEntries")
        return list(entries) if isinstance(entries, list) and entries else list(DEFAULT_CREATION_ENTRIES)

    @classmethod
    def get_format_variants(cls) -> List[Dict[str, Any]]:
        cls.ensure_defaults()
        overrides = cls.get_overrides()
        configured = overrides.get("formatVariants")
        disk_catalog = cls._build_disk_catalog()
        disk_variants = disk_catalog.get("formatVariants") or []
        seed = disk_variants if disk_variants else list(DEFAULT_FORMAT_VARIANTS)

        if not isinstance(configured, list) or not configured:
            return list(seed)

        by_key: Dict[str, Dict[str, Any]] = {}
        for item in seed:
            key = item.get("key")
            if key:
                by_key[key] = dict(item)
        for item in configured:
            key = item.get("key")
            if not key:
                continue
            base = by_key.get(key, {})
            by_key[key] = cls._deep_merge(base, item)

        order = ["A", "B", "C", "D"]
        merged = [by_key[k] for k in order if k in by_key]
        return merged if merged else list(seed)

    @classmethod
    def get_default_format_variant(cls) -> str:
        cls.ensure_defaults()
        value = cls.get_overrides().get("defaultFormatVariant")
        return str(value or DEFAULT_FORMAT_VARIANT_SCHEMA)

    @classmethod
    def get_themes(cls) -> List[Dict[str, Any]]:
        cls.ensure_defaults()
        overrides = cls.get_overrides()
        themes = overrides.get("themes")
        if isinstance(themes, list) and themes:
            return list(themes)
        db_themes = cls._themes_from_db_templates()
        return db_themes or list(themes or [])

    @staticmethod
    def get_episode_settings() -> Dict[str, Any]:
        CreationFormOverrideService.ensure_defaults()
        base = dict(DEFAULT_EPISODE_SETTINGS)
        try:
            overrides = CreationFormOverrideService.get_overrides()
            from_overrides = overrides.get("episodeSettings")
            if isinstance(from_overrides, dict) and from_overrides:
                merged = {**base, **from_overrides}
            else:
                row = CreationFormOverrideService._get_row()
                merged = (
                    {**base, **row.episode_settings}
                    if isinstance(row.episode_settings, dict) and row.episode_settings
                    else base
                )
            presets = merged.get("presets")
            if not isinstance(presets, list) or not presets:
                merged["presets"] = base["presets"]
            return merged
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ != "DatabaseOperationForbidden":
                logger.debug("episode settings DB 读取失败: %s", exc)
        return base

    @staticmethod
    def get_sections() -> Dict[str, Any]:
        CreationFormOverrideService.ensure_defaults()
        sections = CreationFormOverrideService.get_overrides().get("sections")
        return dict(sections) if isinstance(sections, dict) else {}

    @staticmethod
    def get_creation_entry_profiles() -> Dict[str, Any]:
        CreationFormOverrideService.ensure_defaults()
        profiles = {key: dict(value) for key, value in DEFAULT_CREATION_ENTRY_PROFILES.items()}
        configured = CreationFormOverrideService.get_overrides().get("creationEntryProfiles")
        if isinstance(configured, dict):
            for key, value in configured.items():
                if not isinstance(value, dict):
                    continue
                base = profiles.get(key, DEFAULT_CREATION_ENTRY_PROFILES.get("from-scratch", {}))
                profiles[key] = CreationFormOverrideService._deep_merge(base, value)
        return profiles

    @classmethod
    def get_public_catalog_base(cls) -> Dict[str, Any]:
        from apps.workflow.pipeline_store import FusionPipelineDbService

        cls.ensure_defaults()
        return {
            "skillVersion": FusionPipelineDbService.active_version() or "",
            "configSource": FusionPipelineDbService.config_source(),
            "themes": cls.get_themes(),
            "platforms": cls.get_platforms(),
            "formatVariants": cls.get_format_variants(),
            "budgetLevels": cls.get_budget_levels(),
            "creationEntries": cls.get_creation_entries(),
            "episodeSettings": cls.get_episode_settings(),
            "sections": cls.get_sections(),
            "creationEntryProfiles": cls.get_creation_entry_profiles(),
            "defaultFormatVariant": cls.get_default_format_variant(),
        }

    @staticmethod
    def allowed_creation_entries() -> List[str]:
        return [e.get("key") for e in CreationFormOverrideService.get_creation_entries() if e.get("key")]

    @staticmethod
    def creation_entry_profile(entry: str) -> Dict[str, Any]:
        profiles = CreationFormOverrideService.get_creation_entry_profiles()
        return profiles.get(entry) or profiles.get("from-scratch") or {}

    @staticmethod
    def creation_entry_requires_adapt(entry: str) -> bool:
        return bool(CreationFormOverrideService.creation_entry_profile(entry).get("requiresAdapt"))

    @staticmethod
    def creation_entry_validation(entry: str) -> Dict[str, Any]:
        profile = CreationFormOverrideService.creation_entry_profile(entry)
        validation = profile.get("validation") if isinstance(profile, dict) else {}
        return validation if isinstance(validation, dict) else {}

    @staticmethod
    def save_overrides(overrides: Dict[str, Any]) -> Dict[str, Any]:
        row = CreationFormOverrideService._get_row()
        row.overrides = overrides if isinstance(overrides, dict) else {}
        row.save(update_fields=["overrides", "updated_at"])
        CreationFormOverrideService._clear_catalog_cache()
        return row.overrides

    @staticmethod
    def save_episode_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
        row = CreationFormOverrideService._get_row()
        row.episode_settings = settings if isinstance(settings, dict) else {}
        row.save(update_fields=["episode_settings", "updated_at"])
        CreationFormOverrideService._clear_catalog_cache()
        return row.episode_settings

    @staticmethod
    def seed_defaults() -> bool:
        row = CreationFormOverrideService._get_row()
        changed = False
        overrides = dict(row.overrides) if isinstance(row.overrides, dict) else {}

        legacy = CreationFormOverrideService._legacy_overrides()
        if legacy:
            overrides = CreationFormOverrideService._deep_merge(legacy, overrides)
            changed = True

        if not row.episode_settings:
            legacy_eps = CreationFormOverrideService._legacy_episode_settings()
            if legacy_eps:
                row.episode_settings = legacy_eps
                changed = True

        if changed:
            row.overrides = overrides
            row.save()

        if CreationFormOverrideService.import_catalog_from_disk(overwrite=False):
            changed = True
        return changed

    @staticmethod
    def _legacy_overrides() -> Dict[str, Any]:
        try:
            from apps.skill.config.portal.skill_settings import SkillConfigService

            raw = SkillConfigService.get("fusion.creation_form_overrides", "{}") or "{}"
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            logger.debug("fusion.creation_form_overrides 读取失败")
            return {}

    @staticmethod
    def _legacy_episode_settings() -> Dict[str, Any]:
        try:
            from apps.skill.config.portal.skill_settings import SkillConfigService

            raw = SkillConfigService.get("fusion.episode_settings_defaults", "") or ""
            if not raw.strip():
                return {}
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            logger.debug("fusion.episode_settings_defaults 读取失败")
            return {}

    @staticmethod
    def format_variant_schema_key(letter_or_variant: str) -> str:
        if letter_or_variant.startswith("variant-"):
            return letter_or_variant
        return VARIANT_LETTER_MAP.get(str(letter_or_variant or "").upper(), "variant-b")

    @staticmethod
    def format_variant_letter(schema_key: str) -> str:
        return LETTER_FROM_VARIANT.get(schema_key, "B")

    @classmethod
    def format_variant_display(cls, letter_or_variant: str) -> str:
        schema_key = cls.format_variant_schema_key(letter_or_variant)
        for variant in cls.get_format_variants():
            if variant.get("schemaKey") == schema_key:
                return str(variant.get("name") or schema_key)
        return schema_key

    @staticmethod
    def theme_display_name(theme_code: str) -> str:
        for theme in CreationFormOverrideService.get_themes():
            if theme.get("key") == theme_code:
                return str(theme.get("displayName") or theme_code)
        return theme_code

    @staticmethod
    def normalize_platform(value: str) -> str:
        aliases = {
            "wechat": "wechat-miniprogram",
            "multi": "other",
            "tencent-mini": "tencent-mini",
        }
        normalized = aliases.get(value, value)
        allowed = {p.get("key") for p in CreationFormOverrideService.get_platforms()}
        if normalized in allowed:
            return normalized
        return next(iter(allowed)) if allowed else "douyin"
