# -*- coding: utf-8 -*-
"""字段 AI 提示词 — DB 优先，SSOT 默认值兜底。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from apps.skill.config.bootstrap.ai_field_prompts import (
    ADMIN_HIDDEN_FIELD_KEYS,
    DEFAULT_AI_FIELD_PROMPTS,
    resolve_ai_field_display_name,
)
from .models import AiFieldPromptConfig


class AiFieldPromptService:
    @staticmethod
    def resolve_provider_id(action_key: str):
        key = (action_key or "").strip()
        if not key:
            return None
        row = (
            AiFieldPromptConfig.objects.filter(action_key=key, is_active=True)
            .select_related("llm_provider")
            .first()
        )
        if row and row.llm_provider_id and row.llm_provider and row.llm_provider.is_enabled:
            return str(row.llm_provider_id)
        return None

    @staticmethod
    def resolve(action_key: str) -> Optional[Dict[str, Any]]:
        key = (action_key or "").strip()
        if not key:
            return None

        row = AiFieldPromptConfig.objects.filter(action_key=key, is_active=True).first()
        if row:
            return AiFieldPromptService._row_to_meta(row)

        defaults = DEFAULT_AI_FIELD_PROMPTS.get(key)
        if not defaults:
            return None
        return AiFieldPromptService._defaults_to_meta(defaults)

    @staticmethod
    def list_admin_items() -> list:
        rows = {
            r.action_key: r
            for r in AiFieldPromptConfig.objects.select_related("llm_provider").all().order_by(
                "sort_order", "action_key"
            )
        }
        items = []
        keys = sorted(set(DEFAULT_AI_FIELD_PROMPTS.keys()) | set(rows.keys()))
        keys = [k for k in keys if k not in ADMIN_HIDDEN_FIELD_KEYS]
        for idx, key in enumerate(keys):
            row = rows.get(key)
            defaults = DEFAULT_AI_FIELD_PROMPTS.get(key, {})
            stored_name = row.display_name if row else ""
            provider_id = str(row.llm_provider_id) if row and row.llm_provider_id else None
            provider_name = row.llm_provider.name if row and row.llm_provider else None
            items.append(
                {
                    "id": str(row.id) if row else None,
                    "action_key": key,
                    "display_name": resolve_ai_field_display_name(key, stored_name),
                    "system_prompt": row.system_prompt if row else defaults.get("system_prompt", ""),
                    "user_prompt_tpl": row.user_prompt_tpl if row else defaults.get("user_prompt_tpl", ""),
                    "system_prompt_fallback": (
                        row.system_prompt_fallback if row else defaults.get("system_prompt_fallback", "")
                    ),
                    "response_json": row.response_json if row else defaults.get("response_json", False),
                    "is_active": row.is_active if row else True,
                    "sort_order": row.sort_order if row else (idx + 1) * 10,
                    "source": "db" if row else "default",
                    "updated_at": row.updated_at if row else None,
                    "llm_provider_id": provider_id,
                    "llm_provider_name": provider_name,
                }
            )
        return items

    @staticmethod
    def upsert(action_key: str, data: Dict[str, Any]) -> AiFieldPromptConfig:
        key = (action_key or "").strip()
        defaults = DEFAULT_AI_FIELD_PROMPTS.get(key, {})
        canonical_name = resolve_ai_field_display_name(
            key, str(data.get("display_name") or defaults.get("display_name") or "")
        )
        row, _ = AiFieldPromptConfig.objects.update_or_create(
            action_key=key,
            defaults={
                "display_name": canonical_name[:100],
                "system_prompt": str(
                    data.get("system_prompt")
                    if data.get("system_prompt") is not None
                    else defaults.get("system_prompt", "")
                ),
                "user_prompt_tpl": str(
                    data.get("user_prompt_tpl")
                    if data.get("user_prompt_tpl") is not None
                    else defaults.get("user_prompt_tpl", "")
                ),
                "system_prompt_fallback": str(
                    data.get("system_prompt_fallback")
                    if data.get("system_prompt_fallback") is not None
                    else defaults.get("system_prompt_fallback", "")
                ),
                "response_json": bool(
                    data.get("response_json")
                    if "response_json" in data
                    else defaults.get("response_json", False)
                ),
                "is_active": bool(data.get("is_active", True)),
                "sort_order": int(data.get("sort_order") or 0),
            },
        )
        if "llm_provider_id" in data:
            raw = data.get("llm_provider_id")
            if not raw:
                row.llm_provider = None
            else:
                from apps.skill.models import LlmProvider

                row.llm_provider = LlmProvider.objects.filter(pk=raw, is_enabled=True).first()
            row.save(update_fields=["llm_provider", "updated_at"])
        return row

    @staticmethod
    def seed_defaults() -> int:
        created = 0
        for idx, (key, defaults) in enumerate(DEFAULT_AI_FIELD_PROMPTS.items()):
            canonical_name = resolve_ai_field_display_name(key, defaults.get("display_name", ""))
            row, was_created = AiFieldPromptConfig.objects.update_or_create(
                action_key=key,
                defaults={
                    "display_name": canonical_name[:100],
                    "system_prompt": defaults.get("system_prompt", ""),
                    "user_prompt_tpl": defaults.get("user_prompt_tpl", ""),
                    "system_prompt_fallback": defaults.get("system_prompt_fallback", ""),
                    "response_json": defaults.get("response_json", False),
                    "is_active": True,
                    "sort_order": (idx + 1) * 10,
                },
            )
            if was_created:
                created += 1
            elif row.display_name != canonical_name[:100]:
                row.display_name = canonical_name[:100]
                row.save(update_fields=["display_name", "updated_at"])
        return created

    @staticmethod
    def _row_to_meta(row: AiFieldPromptConfig) -> Dict[str, Any]:
        return {
            "system": row.system_prompt,
            "user_tpl": row.user_prompt_tpl,
            "system_text": row.system_prompt_fallback or row.system_prompt,
            "json": row.response_json,
        }

    @staticmethod
    def _defaults_to_meta(defaults: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "system": defaults.get("system_prompt", ""),
            "user_tpl": defaults.get("user_prompt_tpl", ""),
            "system_text": defaults.get("system_prompt_fallback") or defaults.get("system_prompt", ""),
            "json": defaults.get("response_json", False),
        }
