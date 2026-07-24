# -*- coding: utf-8 -*-
"""V3 模型配置适配层：包装 LlmConfigService + 角色映射。"""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.core.exceptions import NOT_FOUND, VALIDATION_ERROR, BusinessException
from apps.drama.models import (
    DramaLlmProvider,
    V3LlmProviderKey,
    V3ModelPrice,
    V3RoleModelMapping,
)
from apps.drama.services.llm_config_service import LlmConfigService
from apps.drama.services.secret_crypto import decrypt_secret, encrypt_secret

MAX_BACKUP_PROVIDERS = 5

V3_ROLE_MODEL_KEYS: tuple[str, ...] = (
    "drama-topic-director",
    "drama-story-bible",
    "drama-episode-designer",
    "drama-script-writer",
    "drama-script-scorer",
    "drama-compliance-guard",
    "drama-revision-master",
    "drama-delivery-tool",
)

_PROVIDER_RESPONSE_KEYS = (
    "id",
    "name",
    "base_url",
    "model_name",
    "temperature",
    "max_tokens",
    "is_enabled",
    "is_active",
    "api_key_set",
    "remark",
    "updated_at",
)


class V3ModelsService:
    """Models REST 业务：Provider CRUD/activate + 角色映射。"""

    @classmethod
    def serialize_provider(cls, obj: DramaLlmProvider) -> dict[str, Any]:
        raw = LlmConfigService.serialize_provider(obj)
        # 契约字段；永不暴露 api_key
        data = {key: raw.get(key) for key in _PROVIDER_RESPONSE_KEYS}
        data.pop("api_key", None)
        return data

    @classmethod
    def list_providers(cls) -> dict[str, Any]:
        items = [
            cls.serialize_provider(p) for p in DramaLlmProvider.objects.all()
        ]
        return {"items": items}

    @classmethod
    def get_provider(cls, provider_id: UUID | str) -> dict[str, Any]:
        obj = get_object_or_404(DramaLlmProvider, pk=provider_id)
        return cls.serialize_provider(obj)

    @classmethod
    def create_provider(cls, data: dict[str, Any], *, actor: str) -> dict[str, Any]:
        obj = LlmConfigService.create_provider(dict(data), actor=actor)
        return cls.serialize_provider(obj)

    @classmethod
    def update_provider(
        cls, provider_id: UUID | str, data: dict[str, Any], *, actor: str
    ) -> dict[str, Any]:
        if not DramaLlmProvider.objects.filter(pk=provider_id).exists():
            raise BusinessException(
                NOT_FOUND, "供应商不存在", http_status=404
            )
        obj = LlmConfigService.update_provider(
            provider_id, dict(data), actor=actor
        )
        return cls.serialize_provider(obj)

    @classmethod
    def delete_provider(cls, provider_id: UUID | str, *, actor: str) -> None:
        if not DramaLlmProvider.objects.filter(pk=provider_id).exists():
            raise BusinessException(
                NOT_FOUND, "供应商不存在", http_status=404
            )
        LlmConfigService.delete_provider(provider_id, actor=actor)

    @classmethod
    def activate_provider(
        cls, provider_id: UUID | str, *, actor: str
    ) -> dict[str, Any]:
        if not DramaLlmProvider.objects.filter(pk=provider_id).exists():
            raise BusinessException(
                NOT_FOUND, "供应商不存在", http_status=404
            )
        obj = LlmConfigService.activate(provider_id, actor=actor)
        return cls.serialize_provider(obj)

    @classmethod
    def _active_provider(cls) -> Optional[DramaLlmProvider]:
        return (
            DramaLlmProvider.objects.filter(is_active=True, is_enabled=True)
            .order_by("-updated_at")
            .first()
        )

    @classmethod
    def _normalize_backup_provider_ids(
        cls,
        raw_ids: Any,
        *,
        primary_provider_id: UUID | str,
    ) -> list[str]:
        if not isinstance(raw_ids, list):
            raise BusinessException(
                VALIDATION_ERROR,
                "backup_provider_ids 必须为数组",
                http_status=400,
            )
        primary_str = str(primary_provider_id)
        seen: set[str] = set()
        normalized: list[str] = []
        for raw in raw_ids:
            backup_id = str(raw)
            if backup_id == primary_str:
                raise BusinessException(
                    VALIDATION_ERROR,
                    "备选供应商不能与主供应商相同",
                    http_status=400,
                )
            if backup_id in seen:
                continue
            seen.add(backup_id)
            normalized.append(backup_id)
            if len(normalized) > MAX_BACKUP_PROVIDERS:
                raise BusinessException(
                    VALIDATION_ERROR,
                    f"备选供应商最多 {MAX_BACKUP_PROVIDERS} 个",
                    http_status=400,
                )
        for backup_id in normalized:
            if not DramaLlmProvider.objects.filter(pk=backup_id).exists():
                raise BusinessException(
                    VALIDATION_ERROR,
                    f"供应商不存在: {backup_id}",
                    http_status=400,
                )
        return normalized

    @classmethod
    def serialize_mapping(cls, obj: V3RoleModelMapping) -> dict[str, Any]:
        return {
            "role_key": obj.role_key,
            "provider_id": str(obj.provider_id),
            "backup_provider_ids": list(obj.backup_provider_ids or []),
            "temperature": obj.temperature,
            "max_tokens": obj.max_tokens,
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        }

    @classmethod
    def list_role_mappings(cls) -> dict[str, Any]:
        """返回 8 个角色键；无行时缺省指向 active provider（若有）。"""
        stored = {
            m.role_key: m
            for m in V3RoleModelMapping.objects.select_related("provider").all()
        }
        active = cls._active_provider()
        items: list[dict[str, Any]] = []
        for role_key in V3_ROLE_MODEL_KEYS:
            mapping = stored.get(role_key)
            if mapping is not None:
                items.append(cls.serialize_mapping(mapping))
                continue
            if active is not None:
                items.append(
                    {
                        "role_key": role_key,
                        "provider_id": str(active.id),
                        "backup_provider_ids": [],
                        "temperature": None,
                        "max_tokens": None,
                        "updated_at": None,
                    }
                )
        return {"items": items}

    @classmethod
    @transaction.atomic
    def put_role_mappings(cls, items: list[dict[str, Any]]) -> dict[str, Any]:
        """批量 upsert 角色映射（按 role_key）。"""
        if not items:
            raise BusinessException(
                VALIDATION_ERROR,
                "items 不能为空",
                http_status=400,
            )
        for raw in items:
            role_key = str(raw.get("role_key") or "").strip()
            if role_key not in V3_ROLE_MODEL_KEYS:
                raise BusinessException(
                    VALIDATION_ERROR,
                    f"非法 role_key: {role_key}",
                    http_status=400,
                )
            provider_id = raw.get("provider_id")
            if not provider_id:
                raise BusinessException(
                    VALIDATION_ERROR,
                    f"{role_key} 缺少 provider_id",
                    http_status=400,
                )
            provider = DramaLlmProvider.objects.filter(pk=provider_id).first()
            if provider is None:
                raise BusinessException(
                    VALIDATION_ERROR,
                    f"供应商不存在: {provider_id}",
                    http_status=400,
                )
            defaults: dict[str, Any] = {"provider": provider}
            if "backup_provider_ids" in raw:
                defaults["backup_provider_ids"] = cls._normalize_backup_provider_ids(
                    raw.get("backup_provider_ids"),
                    primary_provider_id=provider_id,
                )
            if "temperature" in raw:
                defaults["temperature"] = raw.get("temperature")
            if "max_tokens" in raw:
                defaults["max_tokens"] = raw.get("max_tokens")
            V3RoleModelMapping.objects.update_or_create(
                role_key=role_key,
                defaults=defaults,
            )
        return cls.list_role_mappings()

    @classmethod
    def serialize_provider_key(cls, obj: V3LlmProviderKey) -> dict[str, Any]:
        return {
            "id": str(obj.id),
            "provider_id": str(obj.provider_id),
            "label": obj.label,
            "sort_order": obj.sort_order,
            "is_enabled": obj.is_enabled,
            "api_key_set": bool(decrypt_secret(obj.api_key_encrypted)),
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        }

    @classmethod
    def _get_provider_or_404(cls, provider_id: UUID | str) -> DramaLlmProvider:
        provider = DramaLlmProvider.objects.filter(pk=provider_id).first()
        if provider is None:
            raise BusinessException(
                NOT_FOUND, "供应商不存在", http_status=404
            )
        return provider

    @classmethod
    def list_provider_keys(cls, provider_id: UUID | str) -> dict[str, Any]:
        provider = cls._get_provider_or_404(provider_id)
        items = [
            cls.serialize_provider_key(row)
            for row in V3LlmProviderKey.objects.filter(provider=provider).order_by(
                "sort_order", "created_at"
            )
        ]
        return {"items": items}

    @classmethod
    @transaction.atomic
    def create_provider_key(
        cls, provider_id: UUID | str, data: dict[str, Any], *, actor: str
    ) -> dict[str, Any]:
        provider = cls._get_provider_or_404(provider_id)
        api_key = str(data.get("api_key") or "").strip()
        if not api_key:
            raise BusinessException(
                VALIDATION_ERROR, "api_key 不能为空", http_status=400
            )
        obj = V3LlmProviderKey.objects.create(
            provider=provider,
            label=str(data.get("label") or "").strip(),
            api_key_encrypted=encrypt_secret(api_key),
            sort_order=int(data.get("sort_order") or 0),
            is_enabled=bool(data.get("is_enabled", True)),
        )
        return cls.serialize_provider_key(obj)

    @classmethod
    @transaction.atomic
    def update_provider_key(
        cls,
        provider_id: UUID | str,
        key_id: UUID | str,
        data: dict[str, Any],
        *,
        actor: str,
    ) -> dict[str, Any]:
        cls._get_provider_or_404(provider_id)
        obj = (
            V3LlmProviderKey.objects.select_for_update()
            .filter(pk=key_id, provider_id=provider_id)
            .first()
        )
        if obj is None:
            raise BusinessException(
                NOT_FOUND, "密钥不存在", http_status=404
            )
        if "label" in data:
            obj.label = str(data["label"] or "").strip()
        if "sort_order" in data and data["sort_order"] is not None:
            obj.sort_order = int(data["sort_order"])
        if "is_enabled" in data:
            obj.is_enabled = bool(data["is_enabled"])
        api_key = data.get("api_key", None)
        if api_key is not None and str(api_key).strip() != "":
            obj.api_key_encrypted = encrypt_secret(str(api_key).strip())
        obj.save()
        return cls.serialize_provider_key(obj)

    @classmethod
    @transaction.atomic
    def delete_provider_key(
        cls, provider_id: UUID | str, key_id: UUID | str, *, actor: str
    ) -> None:
        cls._get_provider_or_404(provider_id)
        deleted, _ = V3LlmProviderKey.objects.filter(
            pk=key_id, provider_id=provider_id
        ).delete()
        if not deleted:
            raise BusinessException(
                NOT_FOUND, "密钥不存在", http_status=404
            )

    @classmethod
    def serialize_price(cls, obj: V3ModelPrice) -> dict[str, Any]:
        return {
            "id": obj.pk,
            "provider_id": str(obj.provider_id),
            "provider_name": obj.provider.name,
            "model_name": obj.model_name,
            "price_in_per_1k": obj.price_in_per_1k,
            "price_out_per_1k": obj.price_out_per_1k,
            "price_cache_in_per_1k": obj.price_cache_in_per_1k,
            "currency": obj.currency,
        }

    @classmethod
    def list_prices(cls) -> dict[str, Any]:
        rows = V3ModelPrice.objects.select_related("provider").order_by(
            "provider__name", "model_name"
        )
        return {"items": [cls.serialize_price(row) for row in rows]}

    @classmethod
    @transaction.atomic
    def put_prices(cls, items: list[dict[str, Any]]) -> dict[str, Any]:
        """批量 upsert 单价（按 provider_id + model_name）。"""
        if not items:
            raise BusinessException(
                VALIDATION_ERROR,
                "items 不能为空",
                http_status=400,
            )
        for raw in items:
            provider_id = raw.get("provider_id")
            model_name = str(raw.get("model_name") or "").strip()
            if not model_name:
                raise BusinessException(
                    VALIDATION_ERROR,
                    "model_name 不能为空",
                    http_status=400,
                )
            provider = DramaLlmProvider.objects.filter(pk=provider_id).first()
            if provider is None:
                raise BusinessException(
                    VALIDATION_ERROR,
                    f"供应商不存在: {provider_id}",
                    http_status=400,
                )
            V3ModelPrice.objects.update_or_create(
                provider=provider,
                model_name=model_name,
                defaults={
                    "price_in_per_1k": raw["price_in_per_1k"],
                    "price_out_per_1k": raw["price_out_per_1k"],
                    "price_cache_in_per_1k": raw.get("price_cache_in_per_1k"),
                    "currency": raw.get("currency") or "CNY",
                },
            )
        return cls.list_prices()

    @classmethod
    @transaction.atomic
    def delete_price(cls, price_id: int) -> dict[str, Any]:
        deleted, _ = V3ModelPrice.objects.filter(pk=price_id).delete()
        if not deleted:
            raise BusinessException(
                NOT_FOUND, "单价不存在", http_status=404
            )
        return {"deleted": True, "id": price_id}
