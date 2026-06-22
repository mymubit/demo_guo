# -*- coding: utf-8 -*-
"""C 端创作 Catalog SSOT — 从 Fusion 层迁出（skill-agent/02 Phase 3）。"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CreationCatalogService:
    """创作表单 + 公开 Catalog；不再依赖 Fusion 7 节点主链。"""

    @staticmethod
    def themes_for_api() -> List[Dict[str, Any]]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_themes()

    @staticmethod
    def theme_display_name(theme_code: str) -> str:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.theme_display_name(theme_code)

    @staticmethod
    def episode_settings_for_api() -> Dict[str, Any]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_episode_settings()

    @staticmethod
    def sections_for_api() -> Dict[str, Any]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_sections()

    @staticmethod
    def creation_entry_profiles_for_api() -> Dict[str, Any]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        profiles = CreationFormOverrideService.get_creation_entry_profiles()
        entries = CreationCatalogService.creation_entries_for_api()
        entry_keys = [e["key"] for e in entries]
        return {key: profiles[key] for key in entry_keys if key in profiles}

    @staticmethod
    def platforms_for_api() -> List[Dict[str, str]]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_platforms()

    @staticmethod
    def normalize_platform(value: str) -> str:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.normalize_platform(value)

    @staticmethod
    def format_variants_for_api() -> List[Dict[str, Any]]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_format_variants()

    @staticmethod
    def format_variant_schema_key(letter_or_variant: str) -> str:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.format_variant_schema_key(letter_or_variant)

    @staticmethod
    def format_variant_letter(schema_key: str) -> str:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.format_variant_letter(schema_key)

    @staticmethod
    def format_variant_display(letter_or_variant: str) -> str:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.format_variant_display(letter_or_variant)

    @staticmethod
    def budget_levels_for_api() -> List[Dict[str, str]]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_budget_levels()

    @staticmethod
    def creation_entries_for_api() -> List[Dict[str, str]]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_creation_entries()

    @staticmethod
    def public_catalog(*, include_main_chain: bool = False) -> Dict[str, Any]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        catalog = CreationFormOverrideService.get_public_catalog_base()
        catalog["mainChain"] = []
        if include_main_chain:
            logger.warning("CreationCatalogService: mainChain 已废弃，include_main_chain 将被忽略")
        return catalog


def get_creation_form_overrides() -> Dict[str, Any]:
    from apps.skill.config.portal.creation_form import CreationFormOverrideService

    return CreationFormOverrideService.get_overrides()


@lru_cache(maxsize=1)
def get_creation_catalog() -> CreationCatalogService:
    return CreationCatalogService()


def clear_creation_catalog_cache() -> None:
    get_creation_catalog.cache_clear()
    try:
        from apps.workflow.fusion.ssot_catalog import get_ssot_catalog

        get_ssot_catalog.cache_clear()
    except Exception:  # noqa: BLE001
        pass
