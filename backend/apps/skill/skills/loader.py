# -*- coding: utf-8 -*-
"""DB-only skill rule prompt loader — 优先 SkillRuleItem 条目，Config 包兜底。"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

from apps.agent.bootstrap.tier1_sections import resolve_tier1_sections

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
        if key.startswith("_"):
            continue
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
        self._used_rule_item_ids: Dict[str, str] = {}

    def get_tier1(self) -> Dict[str, Any]:
        try:
            from apps.skill.models import SkillRuleConfig
        except Exception as exc:  # noqa: BLE001
            logger.warning("[SkillRuleLoader] get_tier1 unavailable: %s", exc)
            return {}

        merged: Dict[str, Any] = {}
        tier_full = SkillRuleConfig.objects.filter(
            tier=1,
            section="tier_full",
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            status=SkillRuleConfig.STATUS_ACTIVE,
        ).first()
        if tier_full and isinstance(tier_full.content, dict):
            merged.update(tier_full.content)

        for row in SkillRuleConfig.objects.filter(
            tier=1,
            scope_type=SkillRuleConfig.SCOPE_GLOBAL,
            status=SkillRuleConfig.STATUS_ACTIVE,
        ).exclude(section="tier_full"):
            if row.section and isinstance(row.content, dict):
                merged[row.section] = row.content
        return merged

    def _items_for_prompt(
        self,
        *,
        node_id: str = "",
        genre: str = "",
        tiers: Optional[List[int]] = None,
        sections: Optional[List[str]] = None,
    ) -> List[Any]:
        try:
            from apps.skill.models import SkillRuleConfig, SkillRuleItem
        except Exception as exc:  # noqa: BLE001
            logger.warning("[SkillRuleLoader] item model unavailable: %s", exc)
            return []

        qs = SkillRuleItem.objects.filter(
            status=SkillRuleConfig.STATUS_ACTIVE,
            item_type=SkillRuleItem.TYPE_RULE,
        )
        if tiers is not None:
            qs = qs.filter(tier__in=tiers)
        if sections is not None:
            if not sections:
                return []
            qs = qs.filter(section__in=sections)

        rows: List[Any] = []
        for row in qs.order_by("tier", "scope_type", "section", "sort_order", "priority", "-updated_at"):
            if row.tier == 1 and row.scope_type != SkillRuleConfig.SCOPE_GLOBAL:
                continue
            if row.tier == 2:
                if row.scope_type != SkillRuleConfig.SCOPE_GENRE:
                    continue
                if genre and row.scope_key and row.scope_key != genre:
                    continue
            if row.tier == 3:
                if row.scope_type != SkillRuleConfig.SCOPE_NODE:
                    continue
                if node_id and row.scope_key and row.scope_key != node_id:
                    continue
            if row.tier == 4 and row.scope_type != SkillRuleConfig.SCOPE_GLOBAL:
                continue
            rows.append(row)
        return rows

    def _active_configs(
        self,
        *,
        node_id: str = "",
        genre: str = "",
        tiers: Optional[List[int]] = None,
    ) -> List[Any]:
        try:
            from apps.skill.models import SkillRuleConfig
        except Exception as exc:  # noqa: BLE001
            logger.warning("[SkillRuleLoader] config model unavailable: %s", exc)
            return []

        qs = SkillRuleConfig.objects.filter(status=SkillRuleConfig.STATUS_ACTIVE).exclude(
            section__in=("tier_full", "tier1-iron-rules", "tier2-genre-rules", "tier3-workflow-rules")
        )
        if tiers is not None:
            qs = qs.filter(tier__in=tiers)

        rows = []
        for row in qs.order_by("tier", "scope_type", "section", "-updated_at"):
            if row.tier == 1 and row.scope_type == SkillRuleConfig.SCOPE_GLOBAL:
                rows.append(row)
                continue
            if row.tier == 2 and row.scope_type == SkillRuleConfig.SCOPE_GENRE:
                if not genre or not row.scope_key or row.scope_key == genre:
                    rows.append(row)
                continue
            if row.tier == 3 and row.scope_type == SkillRuleConfig.SCOPE_NODE:
                if not node_id or not row.scope_key or row.scope_key == node_id:
                    rows.append(row)
                continue
            if row.tier == 4 and row.scope_type == SkillRuleConfig.SCOPE_GLOBAL:
                rows.append(row)
        return rows

    def _global_content_source(self) -> str:
        try:
            from apps.skill.models import SkillRuleConfig

            row = (
                SkillRuleConfig.objects.filter(status=SkillRuleConfig.STATUS_ACTIVE)
                .order_by("-updated_at")
                .values_list("content_source", flat=True)
                .first()
            )
            return row or SkillRuleConfig.CONTENT_HYBRID
        except Exception as exc:  # noqa: BLE001
            logger.debug("[SkillRuleLoader] content_source fallback: %s", exc)
            return "hybrid"

    def _render_items(self, items: List[Any], *, record_apply: bool) -> List[str]:
        parts: List[str] = []
        applied_ids: List[str] = []
        for row in items:
            body = str(row.body or "").strip()
            if not body:
                continue
            key = row.rule_key
            self._used_rule_item_ids[key] = str(row.id)
            applied_ids.append(str(row.id))
            parts.append(f"[{key}]\n{body}")
        if record_apply and applied_ids:
            try:
                from apps.skill.skills.rule_item_service import SkillRuleItemService

                SkillRuleItemService.record_apply(applied_ids)
            except Exception as exc:  # noqa: BLE001
                logger.debug("[SkillRuleLoader] apply count skipped: %s", exc)
        return parts

    def build_tier1_node_snippet(self, node_id: str) -> str:
        sections = resolve_tier1_sections(node_id)
        items = self._items_for_prompt(node_id=node_id, tiers=[1], sections=sections)
        if items:
            return "\n\n".join(self._render_items(items, record_apply=False))
        parts: List[str] = []
        for row in self._active_configs(node_id=node_id, tiers=[1]):
            if row.section not in sections:
                continue
            content = row.content
            if isinstance(content, dict):
                rendered = _TIER1_RENDERERS.get(row.section or "", _render_section)(content)
            else:
                rendered = str(content or "")
            if rendered.strip():
                parts.append(rendered.strip())
        return "\n\n".join(parts)

    def build_tier4_snippet(self, node_id: str = "") -> str:
        _ = node_id
        items = self._items_for_prompt(tiers=[4])
        if items:
            return "\n\n".join(self._render_items(items, record_apply=False))
        parts: List[str] = []
        for row in self._active_configs(tiers=[4]):
            content = row.content
            if isinstance(content, dict):
                rendered = _render_section(content)
            else:
                rendered = str(content or "")
            if rendered.strip():
                parts.append(rendered.strip())
        return "\n\n".join(parts)

    def build_agent_rules_snippet(self, agent_id: str, *, genre: str = "") -> str:
        """独立 Agent 运行时：按 agent_id 加载 Tier1-4 规则片段（SkillRuleItem 优先）。"""
        from apps.agent.binding import resolve_tier1_sections_for_agent
        from apps.skill.models import SkillRuleConfig
        from apps.skill.skills.agent_scope import node_scope_for_agent

        self._used_rule_config_ids = {}
        self._used_rule_item_ids = {}
        node_id = node_scope_for_agent(agent_id)
        tier1_sections = resolve_tier1_sections_for_agent(agent_id)
        source_mode = self._global_content_source()
        use_items = source_mode in (SkillRuleConfig.CONTENT_ATOMIC, SkillRuleConfig.CONTENT_HYBRID)
        use_configs = source_mode in (SkillRuleConfig.CONTENT_JSON, SkillRuleConfig.CONTENT_HYBRID)

        parts: List[str] = []
        filtered: List[Any] = []
        if use_items:
            items = self._items_for_prompt(node_id=node_id, genre=genre, tiers=[1, 2, 3, 4])
            for row in items:
                if row.tier == 1 and tier1_sections and row.section not in tier1_sections:
                    continue
                filtered.append(row)

        if filtered:
            parts.extend(self._render_items(filtered, record_apply=True))
        elif use_configs:
            for row in self._active_configs(node_id=node_id, genre=genre, tiers=[1, 2, 3, 4]):
                try:
                    from apps.skill.skills.content_source_integrity import verify_hybrid_integrity

                    verify_hybrid_integrity(row)
                except Exception as exc:  # noqa: BLE001
                    logger.debug("[SkillRuleLoader] hybrid verify skipped: %s", exc)
                if row.tier == 1 and tier1_sections and row.section not in tier1_sections:
                    continue
                key = f"tier{row.tier}:{row.section or row.scope_type}:{row.scope_key or 'global'}"
                self._used_rule_config_ids[key] = str(row.id)
                content = row.content
                if isinstance(content, dict):
                    rendered = _TIER1_RENDERERS.get(row.section or "", _render_section)(content)
                else:
                    rendered = str(content or "")
                if rendered.strip():
                    parts.append(f"[Rule {key}]\n{rendered.strip()}")

        return "\n\n".join(part for part in parts if part)

    def build_full_system_prompt(
        self,
        node_id: str,
        genre: str = "",
        role: str = "",
        output_instruction: str = "",
        **_: Any,
    ) -> str:
        self._used_rule_config_ids = {}
        self._used_rule_item_ids = {}
        parts: List[str] = []

        if role:
            parts.append(str(role).strip())

        tier1_sections = resolve_tier1_sections(node_id)
        items = self._items_for_prompt(
            node_id=node_id,
            genre=genre,
            tiers=[1, 2, 3],
            sections=None,
        )
        filtered_items = []
        for row in items:
            if row.tier == 1:
                if not tier1_sections or row.section not in tier1_sections:
                    continue
            filtered_items.append(row)

        if filtered_items:
            parts.extend(self._render_items(filtered_items, record_apply=True))
        else:
            for row in self._active_configs(node_id=node_id, genre=genre, tiers=[1, 2, 3]):
                if row.tier == 1:
                    if not tier1_sections or row.section not in tier1_sections:
                        continue
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

    def used_rule_item_ids(self) -> Dict[str, str]:
        return dict(self._used_rule_item_ids)

    def get_used_rule_config_ids(self) -> Dict[str, str]:
        return self.used_rule_config_ids()


_loader_instance: Optional[SkillRuleLoader] = None


def get_skill_rule_loader() -> SkillRuleLoader:
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = SkillRuleLoader()
    return _loader_instance
