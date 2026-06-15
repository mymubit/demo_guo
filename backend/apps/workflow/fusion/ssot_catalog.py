# -*- coding: utf-8 -*-
"""C 端融合 Catalog — 运行时只读 DB（CreationFormOverrideConfig + FusionPipelinePack）。"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

from .config_loader import FusionSkillConfig, get_fusion_config
from .schema_registry import FusionSchemaRegistry

logger = logging.getLogger(__name__)


class FusionSsotCatalog:
    def __init__(self, config: Optional[FusionSkillConfig] = None):
        self.config = config or get_fusion_config()

    def _load_schema(self, schema_file: str) -> dict:
        from apps.workflow.pipeline_store import FusionPipelineDbService

        rel = schema_file.replace("schemas/", "")
        if FusionPipelineDbService.should_use_db():
            data = FusionPipelineDbService.get_schema_dict(rel)
            if data is not None:
                return data
        return {}

    def themes_for_api(self) -> List[Dict[str, Any]]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_themes()

    def theme_display_name(self, theme_code: str) -> str:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.theme_display_name(theme_code)

    def episode_settings_for_api(self) -> Dict[str, Any]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_episode_settings()

    def sections_for_api(self) -> Dict[str, Any]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_sections()

    def creation_entry_profiles_for_api(self) -> Dict[str, Any]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        profiles = CreationFormOverrideService.get_creation_entry_profiles()
        entry_keys = [e["key"] for e in self.creation_entries_for_api()]
        return {key: profiles[key] for key in entry_keys if key in profiles}

    def platforms_for_api(self) -> List[Dict[str, str]]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_platforms()

    def normalize_platform(self, value: str) -> str:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.normalize_platform(value)

    def format_variants_for_api(self) -> List[Dict[str, Any]]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_format_variants()

    def format_variant_schema_key(self, letter_or_variant: str) -> str:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.format_variant_schema_key(letter_or_variant)

    def format_variant_letter(self, schema_key: str) -> str:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.format_variant_letter(schema_key)

    def format_variant_display(self, letter_or_variant: str) -> str:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.format_variant_display(letter_or_variant)

    def budget_levels_for_api(self) -> List[Dict[str, str]]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_budget_levels()

    def creation_entries_for_api(self) -> List[Dict[str, str]]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        return CreationFormOverrideService.get_creation_entries()

    def node_llm_prompts(self) -> Dict[str, Any]:
        from apps.workflow.step_admin import PipelineStepAdminService

        return PipelineStepAdminService.build_prompts_dict()

    def public_catalog(self) -> Dict[str, Any]:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        reg = FusionSchemaRegistry(self.config)
        catalog = CreationFormOverrideService.get_public_catalog_base()
        catalog["mainChain"] = reg.nodes_for_api()
        catalog["artifactKeys"] = reg.main_chain_artifact_keys()
        return catalog


def get_creation_form_overrides() -> Dict[str, Any]:
    from apps.skill.config.portal.creation_form import CreationFormOverrideService

    return CreationFormOverrideService.get_overrides()


@lru_cache(maxsize=1)
def get_ssot_catalog() -> FusionSsotCatalog:
    return FusionSsotCatalog()
