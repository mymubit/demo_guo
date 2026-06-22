# -*- coding: utf-8 -*-
"""C 端融合 Catalog — 兼容层，委托 CreationCatalogService（skill-agent/02）。"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEPRECATION_LOGGED = False


def _log_deprecation_once() -> None:
    global _DEPRECATION_LOGGED
    if _DEPRECATION_LOGGED:
        return
    _DEPRECATION_LOGGED = True
    logger.info(
        "apps.workflow.fusion.ssot_catalog 为兼容层，请改用 apps.skill.config.portal.creation_catalog"
    )


class FusionSsotCatalog:
    """Deprecated: 使用 CreationCatalogService。"""

    def __init__(self, config=None):
        _log_deprecation_once()
        self.config = config

    def themes_for_api(self) -> List[Dict[str, Any]]:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().themes_for_api()

    def theme_display_name(self, theme_code: str) -> str:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().theme_display_name(theme_code)

    def episode_settings_for_api(self) -> Dict[str, Any]:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().episode_settings_for_api()

    def sections_for_api(self) -> Dict[str, Any]:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().sections_for_api()

    def creation_entry_profiles_for_api(self) -> Dict[str, Any]:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().creation_entry_profiles_for_api()

    def platforms_for_api(self) -> List[Dict[str, str]]:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().platforms_for_api()

    def normalize_platform(self, value: str) -> str:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().normalize_platform(value)

    def format_variants_for_api(self) -> List[Dict[str, Any]]:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().format_variants_for_api()

    def format_variant_schema_key(self, letter_or_variant: str) -> str:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().format_variant_schema_key(letter_or_variant)

    def format_variant_letter(self, schema_key: str) -> str:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().format_variant_letter(schema_key)

    def format_variant_display(self, letter_or_variant: str) -> str:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().format_variant_display(letter_or_variant)

    def budget_levels_for_api(self) -> List[Dict[str, str]]:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().budget_levels_for_api()

    def creation_entries_for_api(self) -> List[Dict[str, str]]:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().creation_entries_for_api()

    def node_llm_prompts(self) -> Dict[str, Any]:
        from apps.workflow.step_admin import PipelineStepAdminService

        return PipelineStepAdminService.build_prompts_dict()

    def public_catalog(self) -> Dict[str, Any]:
        from apps.skill.config.portal.creation_catalog import get_creation_catalog

        return get_creation_catalog().public_catalog()


def get_creation_form_overrides() -> Dict[str, Any]:
    from apps.skill.config.portal.creation_catalog import get_creation_form_overrides as _fn

    return _fn()


@lru_cache(maxsize=1)
def get_ssot_catalog() -> FusionSsotCatalog:
    _log_deprecation_once()
    return FusionSsotCatalog()
