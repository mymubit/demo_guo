# -*- coding: utf-8 -*-
"""AgentSkillSection → content 同步（skill-agent/12 §4.1）。"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.skill.models import AgentSkillDefinition


def sync_content_from_sections(skill: "AgentSkillDefinition") -> str:
    from apps.skill.models_catalog import AgentSkillSection

    parts: list[str] = []
    for row in AgentSkillSection.objects.filter(skill=skill, is_active=True).order_by("sort_order", "section_key"):
        header = f"## {row.get_section_key_display()}"
        body = (row.section_content or "").strip()
        if row.section_schema_json:
            import json

            body = body or json.dumps(row.section_schema_json, ensure_ascii=False, indent=2)
        if body:
            parts.append(f"{header}\n{body}")
    content = "\n\n".join(parts).strip()
    if content and content != (skill.content or ""):
        skill.content = content
        skill.save(update_fields=["content", "updated_at"])
    return content or skill.content or ""
