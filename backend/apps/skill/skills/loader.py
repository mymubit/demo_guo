# -*- coding: utf-8 -*-
"""DB-only skill rule prompt loader for the ScriptForge runtime."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

_PERMANENT_CACHE: Dict[str, Any] = {}
_HOT_RELOAD_CACHE: Dict[str, Dict[str, Any]] = {}
_HOT_RELOAD_MTIME: Dict[str, float] = {}


def _get_rules_root() -> Path:
    return Path(getattr(settings, "SCRIPT_FORGE_ASSET_ROOT", "")) / "skill-rules"


def _render_section(data: Dict[str, Any]) -> str:
    if not isinstance(data, dict) or not data:
        return ""
    lines: List[str] = []
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = str(value)
        lines.append(f"- {key}: {rendered}")
    return "\n".join(lines)


_TIER1_RENDERERS = {
    "philosophy": _render_section,
    "rhythm_rules": _render_section,
    "episode_structure": _render_section,
    "character_rules": _render_section,
    "genre_rules": _render_section,
    "compliance": _render_section,
    "scoring": _render_section,
}


class SkillRuleLoader:
    def __init__(self) -> None:
        self._used_rule_config_ids: Dict[str, str] = {}

    def _active_rules(self, *, node_id: str = "", genre: str = "") -> List[Any]:
        try:
            from apps.skill.models import SkillRuleConfig
        except Exception as exc:  # noqa: BLE001
            logger.warning("[SkillRuleLoader] model unavailable: %s", exc)
            return []

        scopes = [SkillRuleConfig.SCOPE_GLOBAL]
        if genre:
            scopes.append(SkillRuleConfig.SCOPE_GENRE)
        if node_id:
            scopes.append(SkillRuleConfig.SCOPE_NODE)
        qs = SkillRuleConfig.objects.filter(
            status=SkillRuleConfig.STATUS_ACTIVE,
            scope_type__in=scopes,
        ).order_by("tier", "scope_type", "section", "-updated_at")
        rows = []
        for row in qs:
            if row.scope_type == SkillRuleConfig.SCOPE_GENRE and row.scope_key and row.scope_key != genre:
                continue
            if row.scope_type == SkillRuleConfig.SCOPE_NODE and row.scope_key and row.scope_key != node_id:
                continue
            rows.append(row)
        return rows

    def build_full_system_prompt(
        self,
        node_id: str,
        genre: str = "",
        role: str = "",
        output_instruction: str = "",
        **_: Any,
    ) -> str:
        self._used_rule_config_ids = {}
        parts: List[str] = []
        if role:
            parts.append(str(role).strip())

        for row in self._active_rules(node_id=node_id, genre=genre):
            key = f"tier{row.tier}:{row.section or row.scope_type}:{row.scope_key or 'global'}"
            self._used_rule_config_ids[key] = str(row.id)
            title = f"[Rule {key}]"
            content = row.content
            if isinstance(content, dict):
                rendered = _TIER1_RENDERERS.get(row.section or "", _render_section)(content)
            else:
                rendered = str(content or "")
            if rendered.strip():
                parts.append(f"{title}\n{rendered.strip()}")

        if output_instruction:
            parts.append(str(output_instruction).strip())
        return "\n\n".join(part for part in parts if part)

    def used_rule_config_ids(self) -> Dict[str, str]:
        return dict(self._used_rule_config_ids)

    def get_used_rule_config_ids(self) -> Dict[str, str]:
        return self.used_rule_config_ids()


_loader_instance: Optional[SkillRuleLoader] = None


def get_skill_rule_loader() -> SkillRuleLoader:
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = SkillRuleLoader()
    return _loader_instance
