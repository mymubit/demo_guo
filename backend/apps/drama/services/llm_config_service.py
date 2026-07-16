# -*- coding: utf-8 -*-
"""LLM Provider 配置读写服务。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from django.db import transaction

from apps.drama.models import DramaAuditEvent, DramaLlmProvider
from apps.drama.services.secret_crypto import decrypt_secret, encrypt_secret


@dataclass(frozen=True)
class ResolvedLlmConfig:
    enabled: bool
    base_url: str
    api_key: str
    model: str
    temperature: float
    max_tokens: int
    source: str  # db | env | none


class LlmConfigService:
    """解析当前生效的 LLM 配置：active DB > settings.env。"""

    @classmethod
    def resolve(cls) -> ResolvedLlmConfig:
        from django.conf import settings

        active = (
            DramaLlmProvider.objects.filter(is_active=True, is_enabled=True)
            .order_by("-updated_at")
            .first()
        )
        if active:
            api_key = decrypt_secret(active.api_key_encrypted) or ""
            return ResolvedLlmConfig(
                enabled=True,
                base_url=(active.base_url or "").strip(),
                api_key=api_key,
                model=(active.model_name or "").strip() or "gpt-4o-mini",
                temperature=float(active.temperature),
                max_tokens=int(active.max_tokens),
                source="db",
            )

        if not settings.LLM_ENABLED:
            return ResolvedLlmConfig(
                enabled=False,
                base_url="",
                api_key="",
                model="",
                temperature=0.7,
                max_tokens=4096,
                source="none",
            )

        return ResolvedLlmConfig(
            enabled=True,
            base_url=(settings.LLM_API_BASE_URL or "").strip(),
            api_key=(settings.LLM_API_KEY or "").strip(),
            model=(settings.LLM_MODEL or "gpt-4o-mini").strip(),
            temperature=0.7,
            max_tokens=4096,
            source="env",
        )

    @classmethod
    def serialize_provider(cls, obj: DramaLlmProvider) -> dict[str, Any]:
        return {
            "id": str(obj.id),
            "name": obj.name,
            "base_url": obj.base_url,
            "model_name": obj.model_name,
            "api_key_set": bool(decrypt_secret(obj.api_key_encrypted)),
            "temperature": obj.temperature,
            "max_tokens": obj.max_tokens,
            "is_enabled": obj.is_enabled,
            "is_active": obj.is_active,
            "remark": obj.remark,
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        }

    @classmethod
    def list_providers(cls) -> list[dict[str, Any]]:
        return [cls.serialize_provider(p) for p in DramaLlmProvider.objects.all()]

    @classmethod
    @transaction.atomic
    def create_provider(cls, data: dict[str, Any], *, actor: str) -> DramaLlmProvider:
        api_key = data.pop("api_key", None)
        make_active = bool(data.pop("is_active", False))
        obj = DramaLlmProvider(**data)
        if api_key:
            obj.api_key_encrypted = encrypt_secret(api_key)
        obj.save()
        if make_active:
            cls.activate(obj.id, actor=actor)
            obj.refresh_from_db()
        DramaAuditEvent.objects.create(
            actor=actor,
            action="llm_provider.create",
            detail={"id": str(obj.id), "name": obj.name},
        )
        return obj

    @classmethod
    @transaction.atomic
    def update_provider(
        cls, provider_id, data: dict[str, Any], *, actor: str
    ) -> DramaLlmProvider:
        obj = DramaLlmProvider.objects.select_for_update().get(pk=provider_id)
        api_key = data.pop("api_key", None)
        make_active = data.pop("is_active", None)
        for key, value in data.items():
            setattr(obj, key, value)
        if api_key is not None and str(api_key).strip() != "":
            obj.api_key_encrypted = encrypt_secret(str(api_key))
        obj.save()
        if make_active is True:
            cls.activate(obj.id, actor=actor)
            obj.refresh_from_db()
        elif make_active is False:
            obj.is_active = False
            obj.save(update_fields=["is_active", "updated_at"])
        DramaAuditEvent.objects.create(
            actor=actor,
            action="llm_provider.update",
            detail={"id": str(obj.id), "name": obj.name},
        )
        return obj

    @classmethod
    @transaction.atomic
    def delete_provider(cls, provider_id, *, actor: str) -> None:
        obj = DramaLlmProvider.objects.filter(pk=provider_id).first()
        if not obj:
            return
        DramaAuditEvent.objects.create(
            actor=actor,
            action="llm_provider.delete",
            detail={"id": str(obj.id), "name": obj.name},
        )
        obj.delete()

    @classmethod
    @transaction.atomic
    def activate(cls, provider_id, *, actor: str) -> DramaLlmProvider:
        obj = DramaLlmProvider.objects.select_for_update().get(pk=provider_id)
        DramaLlmProvider.objects.exclude(pk=obj.pk).filter(is_active=True).update(
            is_active=False
        )
        obj.is_active = True
        obj.is_enabled = True
        obj.save(update_fields=["is_active", "is_enabled", "updated_at"])
        DramaAuditEvent.objects.create(
            actor=actor,
            action="llm_provider.activate",
            detail={"id": str(obj.id), "name": obj.name},
        )
        return obj
