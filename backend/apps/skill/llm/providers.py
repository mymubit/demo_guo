# -*- coding: utf-8 -*-
"""多模型 LLM 配置读写与当前启用项切换。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db import transaction

from apps.skill.models import LlmModelCatalog, LlmProvider
from apps.skill.config.portal.skill_settings import SkillConfigService
from apps.skill.llm.volcengine_config import (
    VOLCANO_KEY_CODING_PLAN,
    VOLCANO_KEY_PAYG,
    effective_volcano_base_url,
    infer_volcano_key_type,
    is_volcano_host,
    resolve_volcano_base_url,
)

logger = logging.getLogger(__name__)


class LlmProviderError(Exception):
    pass


class LlmProviderService:
    @staticmethod
    def normalize_base_url(endpoint: str) -> str:
        return SkillConfigService._normalize_llm_base_url(endpoint or "")

    @classmethod
    def _is_volcano_provider(cls, row: LlmProvider) -> bool:
        if row.catalog_id and row.catalog.vendor == "volcengine":
            return True
        return is_volcano_host(row.base_url)

    @classmethod
    def _apply_volcano_fields(cls, row: LlmProvider, data: Dict[str, Any]) -> None:
        if "volcano_key_type" in data:
            row.volcano_key_type = str(data.get("volcano_key_type") or "").strip()[:32]

        is_volcano = cls._is_volcano_provider(row)
        if not is_volcano and "base_url" in data:
            is_volcano = is_volcano_host(str(data.get("base_url") or row.base_url or ""))

        if not is_volcano:
            return

        if row.volcano_key_type in {VOLCANO_KEY_PAYG, VOLCANO_KEY_CODING_PLAN}:
            row.base_url = resolve_volcano_base_url(row.volcano_key_type)
        elif row.base_url:
            inferred = infer_volcano_key_type(row.base_url)
            if inferred:
                row.volcano_key_type = inferred

    @classmethod
    def _effective_base_url(cls, row: LlmProvider) -> str:
        base_url = cls.normalize_base_url(row.base_url)
        if cls._is_volcano_provider(row) or is_volcano_host(base_url):
            return effective_volcano_base_url(
                base_url=base_url,
                key_type=row.volcano_key_type or infer_volcano_key_type(base_url),
            )
        return base_url

    @classmethod
    def global_enabled(cls) -> bool:
        try:
            flag = SkillConfigService.get("llm.enabled", "false").lower()
        except Exception:  # noqa: BLE001
            flag = "false"
        return flag in ("1", "true", "yes")

    @classmethod
    def set_global_enabled(cls, enabled: bool) -> None:
        SkillConfigService.set("llm.enabled", "true" if enabled else "false")

    @classmethod
    def list_providers(cls) -> List[LlmProvider]:
        return list(LlmProvider.objects.select_related("catalog").all().order_by("sort_order", "-created_at"))

    @classmethod
    def get_active(cls) -> Optional[LlmProvider]:
        active = LlmProvider.objects.filter(is_active=True, is_enabled=True).first()
        if active:
            return active
        return (
            LlmProvider.objects.filter(is_enabled=True)
            .order_by("sort_order", "-created_at")
            .first()
        )

    @classmethod
    def get_by_id(cls, provider_id) -> Optional[LlmProvider]:
        try:
            return LlmProvider.objects.get(pk=provider_id)
        except LlmProvider.DoesNotExist:
            return None

    @classmethod
    def runtime_config(cls, provider: Optional[LlmProvider] = None) -> Dict[str, Any]:
        row = provider or cls.get_active()
        if row is None:
            return cls._empty_runtime_config()

        from apps.skill.llm.vendor_keys import (
            LlmVendorCredentialService,
            resolve_provider_vendor,
        )

        api_key = row.get_api_key() or ""
        vendor = resolve_provider_vendor(row)
        if not api_key and vendor:
            api_key = LlmVendorCredentialService.get_api_key(vendor) or ""
        base_url = cls._effective_base_url(row)
        catalog_preset_key = ""
        if row.catalog_id:
            catalog_preset_key = getattr(row.catalog, "preset_key", "") or ""

        configured_model = row.model_name or "gpt-4o-mini"
        key_type = row.volcano_key_type or ""
        if vendor == "volcengine" and not key_type:
            key_type = LlmVendorCredentialService.get_volcano_key_type("volcengine")

        from apps.skill.llm.volcengine_chat import resolve_volcano_chat_model

        resolved_model = resolve_volcano_chat_model(
            model=configured_model,
            catalog_preset_key=catalog_preset_key,
            volcano_key_type=key_type,
            base_url=base_url,
        )

        return {
            "provider_id": str(row.id),
            "provider_name": row.name,
            "vendor": vendor or "",
            "catalog_preset_key": catalog_preset_key,
            "api_key": api_key,
            "base_url": base_url,
            "model": resolved_model,
            "model_configured": configured_model,
            "temperature": float(row.temperature or 0.7),
            "max_tokens": int(row.max_tokens or 4096),
            "volcano_key_type": key_type or row.volcano_key_type or "",
        }

    @classmethod
    def _empty_runtime_config(cls) -> Dict[str, Any]:
        return {
            "provider_id": None,
            "provider_name": "",
            "vendor": "",
            "catalog_preset_key": "",
            "api_key": "",
            "base_url": "",
            "model": "",
            "model_configured": "",
            "temperature": 0.7,
            "max_tokens": 4096,
            "volcano_key_type": "",
        }

    @classmethod
    def is_ready(cls) -> bool:
        if not getattr(settings, "FUSION_LLM_ENABLED", True):
            return False
        if not cls.global_enabled():
            return False
        cfg = cls.runtime_config()
        return bool(cfg.get("api_key") and cfg.get("base_url"))

    @classmethod
    def status_payload(cls) -> Dict[str, Any]:
        active = cls.get_active()
        cfg = cls.runtime_config(active)
        return {
            "fusion_llm_enabled": bool(getattr(settings, "FUSION_LLM_ENABLED", True)),
            "global_enabled": cls.global_enabled(),
            "is_enabled": cls.global_enabled() and bool(getattr(settings, "FUSION_LLM_ENABLED", True)),
            "is_configured": bool(cfg.get("api_key") and cfg.get("base_url")),
            "ready": cls.is_ready(),
            "active_provider_id": str(active.id) if active else None,
            "active_provider_name": active.name if active else None,
        }

    @classmethod
    def provider_has_api_key(cls, row: LlmProvider) -> bool:
        if row.api_key_set:
            return True
        from apps.skill.llm.vendor_keys import (
            LlmVendorCredentialService,
            resolve_provider_vendor,
        )

        vendor = resolve_provider_vendor(row)
        return bool(vendor and LlmVendorCredentialService.api_key_set(vendor))

    @classmethod
    def serialize(cls, row: LlmProvider, *, include_api_key: bool = False) -> Dict[str, Any]:
        data = {
            "id": str(row.id),
            "catalog_id": str(row.catalog_id) if row.catalog_id else None,
            "name": row.name,
            "provider_type": row.provider_type,
            "base_url": row.base_url,
            "model_name": row.model_name,
            "temperature": row.temperature,
            "max_tokens": row.max_tokens,
            "context_window_input": row.context_window_input,
            "context_window_output": row.context_window_output,
            "tool_call_rounds": row.tool_call_rounds,
            "supports_multimodal": row.supports_multimodal,
            "is_active": row.is_active,
            "is_enabled": row.is_enabled,
            "sort_order": row.sort_order,
            "remark": row.remark,
            "api_key_set": row.api_key_set,
            "vendor_api_key_set": cls.provider_has_api_key(row),
            "volcano_key_type": row.volcano_key_type or "",
            "vendor": row.catalog.vendor if row.catalog_id else "",
            "vendor_label": (row.catalog.vendor_label or row.catalog.vendor) if row.catalog_id else "",
            "catalog_input_price_per_million": (
                str(row.catalog.input_price_per_million)
                if row.catalog_id and row.catalog.input_price_per_million is not None
                else None
            ),
            "catalog_output_price_per_million": (
                str(row.catalog.output_price_per_million)
                if row.catalog_id and row.catalog.output_price_per_million is not None
                else None
            ),
            "catalog_preset_key": row.catalog.preset_key if row.catalog_id else None,
            "updated_at": row.updated_at,
        }
        if include_api_key:
            data["api_key"] = row.get_api_key() or ""
        return data

    @classmethod
    def _apply_catalog_defaults(cls, row: LlmProvider, catalog: LlmModelCatalog) -> None:
        from apps.skill.llm.model_catalog import LlmCatalogService

        defaults = LlmCatalogService.defaults_for_provider(catalog)
        row.catalog = catalog
        row.name = defaults["name"]
        row.base_url = defaults["base_url"]
        row.model_name = defaults["model_name"]
        row.temperature = defaults["temperature"]
        row.max_tokens = defaults["max_tokens"]
        row.context_window_input = defaults.get("context_window_input")
        row.context_window_output = defaults.get("context_window_output")
        row.tool_call_rounds = defaults.get("tool_call_rounds")
        row.supports_multimodal = defaults.get("supports_multimodal", False)
        if not row.remark:
            row.remark = defaults.get("remark", "")[:255]
        row.sort_order = defaults.get("sort_order", row.sort_order)

    @classmethod
    @transaction.atomic
    def create_provider(cls, data: Dict[str, Any]) -> LlmProvider:
        catalog = None
        catalog_id = data.get("catalog_id")
        if catalog_id:
            catalog = LlmModelCatalog.objects.filter(pk=catalog_id, is_enabled=True).first()
            if catalog is None:
                raise LlmProviderError("指定的模型目录不存在或已停用")

        row = LlmProvider(
            name=str(data.get("name") or "未命名模型").strip()[:100],
            provider_type=data.get("provider_type") or LlmProvider.PROVIDER_OPENAI_COMPAT,
            base_url=cls.normalize_base_url(str(data.get("base_url") or "")),
            model_name=str(data.get("model_name") or "gpt-4o-mini").strip()[:128],
            temperature=float(data.get("temperature", 0.7) or 0.7),
            max_tokens=max(256, int(data.get("max_tokens", 4096) or 4096)),
            is_enabled=bool(data.get("is_enabled", True)),
            sort_order=int(data.get("sort_order", 0) or 0),
            remark=str(data.get("remark") or "")[:255],
            volcano_key_type=str(data.get("volcano_key_type") or "")[:32],
            context_window_input=data.get("context_window_input"),
            context_window_output=data.get("context_window_output"),
            tool_call_rounds=data.get("tool_call_rounds"),
            supports_multimodal=bool(data.get("supports_multimodal", False)),
        )
        if catalog:
            cls._apply_catalog_defaults(row, catalog)
            for field in ("temperature", "max_tokens", "context_window_input", "context_window_output", "tool_call_rounds", "supports_multimodal", "remark", "name"):
                if field in data and data[field] not in (None, ""):
                    if field in ("context_window_input", "context_window_output", "tool_call_rounds"):
                        row.__setattr__(field, int(data[field]) if data[field] else None)
                    elif field == "supports_multimodal":
                        row.supports_multimodal = bool(data[field])
                    elif field == "max_tokens":
                        row.max_tokens = max(256, int(data[field]))
                    elif field == "temperature":
                        row.temperature = float(data[field])
                    else:
                        row.__setattr__(field, str(data[field])[:255] if field == "remark" else str(data[field])[:100])
        api_key = str(data.get("api_key") or "").strip()
        if api_key:
            row.set_api_key(api_key)
        cls._apply_volcano_fields(row, data)
        from apps.skill.llm.vendor_keys import LlmVendorCredentialService

        LlmVendorCredentialService.inherit_api_key_for_provider(row)
        row.save()
        if row.api_key_set and (
            data.get("set_active") or not LlmProvider.objects.filter(is_active=True).exists()
        ):
            try:
                cls.set_active(row.id)
            except LlmProviderError:
                pass
        return row

    @classmethod
    @transaction.atomic
    def update_provider(cls, provider_id, data: Dict[str, Any]) -> LlmProvider:
        row = cls.get_by_id(provider_id)
        if row is None:
            raise LlmProviderError("模型配置不存在")

        if "name" in data:
            row.name = str(data["name"] or row.name).strip()[:100]
        if "provider_type" in data:
            row.provider_type = data["provider_type"] or row.provider_type
        if "base_url" in data:
            row.base_url = cls.normalize_base_url(str(data["base_url"] or ""))
        if "model_name" in data:
            row.model_name = str(data["model_name"] or row.model_name).strip()[:128]
        cls._apply_volcano_fields(row, data)
        if "temperature" in data:
            row.temperature = float(data["temperature"] or row.temperature)
        if "max_tokens" in data:
            row.max_tokens = max(256, int(data["max_tokens"] or row.max_tokens))
        for int_field in ("context_window_input", "context_window_output", "tool_call_rounds"):
            if int_field in data:
                val = data[int_field]
                row.__setattr__(int_field, int(val) if val not in (None, "") else None)
        if "supports_multimodal" in data:
            row.supports_multimodal = bool(data["supports_multimodal"])
        if "is_enabled" in data:
            row.is_enabled = bool(data["is_enabled"])
        if "sort_order" in data:
            row.sort_order = int(data["sort_order"] or 0)
        if "remark" in data:
            row.remark = str(data["remark"] or "")[:255]
        if "api_key" in data:
            val = str(data["api_key"] or "").strip()
            if val and val != "******":
                row.set_api_key(val)
        cls._apply_volcano_fields(row, data)
        row.save()

        if data.get("set_active"):
            cls.set_active(row.id)
        elif row.is_active and not row.is_enabled:
            row.is_active = False
            row.save(update_fields=["is_active", "updated_at"])
        return row

    @classmethod
    @transaction.atomic
    def delete_provider(cls, provider_id) -> None:
        row = cls.get_by_id(provider_id)
        if row is None:
            raise LlmProviderError("模型配置不存在")
        was_active = row.is_active
        row.delete()
        if was_active:
            nxt = LlmProvider.objects.filter(is_enabled=True).order_by("sort_order", "-created_at").first()
            if nxt:
                cls.set_active(nxt.id)

    @classmethod
    @transaction.atomic
    def set_active(cls, provider_id) -> LlmProvider:
        row = cls.get_by_id(provider_id)
        if row is None:
            raise LlmProviderError("模型配置不存在")
        if not row.is_enabled:
            raise LlmProviderError("该模型已停用，请先启用后再设为当前使用")
        if not row.api_key_set or not row.base_url:
            raise LlmProviderError("请先补全 API Key 与 Base URL")
        LlmProvider.objects.filter(is_active=True).update(is_active=False)
        row.is_active = True
        row.save(update_fields=["is_active", "updated_at"])
        return row

    @classmethod
    @transaction.atomic
    def apply_detected_volcano_config(
        cls,
        provider_id,
        *,
        base_url: str,
        key_type: str,
    ) -> LlmProvider:
        return cls.update_provider(
            provider_id,
            {
                "base_url": base_url,
                "volcano_key_type": key_type,
            },
        )

    @classmethod
    def list_presets(cls) -> List[Dict[str, Any]]:
        from apps.skill.llm.model_catalog import LlmCatalogService

        return LlmCatalogService.list_presets_with_status()

    @classmethod
    def ensure_builtin_presets(cls) -> int:
        """确保目录种子存在，并为目录项创建未配置的接入实例（无 API Key）。"""
        from apps.skill.llm.model_catalog import LlmCatalogService

        LlmCatalogService.ensure_seed_catalog()
        created = 0
        for catalog in LlmCatalogService.list_catalog(enabled_only=True):
            base_url = cls.normalize_base_url(catalog.base_url)
            if LlmProvider.objects.filter(base_url=base_url, model_name=catalog.model_name).exists():
                continue
            row = LlmProvider(is_enabled=True, is_active=False)
            cls._apply_catalog_defaults(row, catalog)
            row.save()
            created += 1
        if created:
            logger.info("已从目录写入 %d 个大模型接入项", created)
        return created

    @classmethod
    def migrate_legacy_skill_config(cls) -> None:
        if LlmProvider.objects.exists():
            return

        def _get(key: str, default: str = "") -> str:
            try:
                return SkillConfigService.get(key, default) or default
            except Exception:  # noqa: BLE001
                return default

        api_key = _get("llm.api_key", "")
        base_url = cls.normalize_base_url(_get("llm.base_url", ""))
        if not api_key and not base_url:
            return

        row = LlmProvider(
            name="默认模型",
            base_url=base_url,
            model_name=_get("llm.model_name", "gpt-4o-mini"),
            temperature=float(_get("llm.temperature", "0.7") or 0.7),
            max_tokens=int(_get("llm.max_tokens", "4096") or 4096),
            is_active=True,
            is_enabled=True,
            sort_order=0,
            remark="由旧版 llm.* 配置迁移",
        )
        if api_key:
            row.set_api_key(api_key)
        row.save()
        logger.info("已将旧版 SkillConfig LLM 配置迁移为 LlmProvider: %s", row.id)

    @classmethod
    def ensure_default_from_env(cls) -> None:
        endpoint = getattr(settings, "LLM_API_ENDPOINT", "") or ""
        api_key = getattr(settings, "LLM_API_KEY", "") or ""
        if not endpoint and not api_key:
            return

        base_url = cls.normalize_base_url(endpoint)
        existing = LlmProvider.objects.filter(base_url=base_url, model_name="gpt-4o-mini").first()
        if existing:
            if api_key:
                existing.set_api_key(api_key)
                existing.save()
            if not LlmProvider.objects.filter(is_active=True).exists():
                cls.set_active(existing.id)
            return

        row = cls.create_provider(
            {
                "name": "环境变量默认",
                "api_key": api_key,
                "base_url": base_url,
                "model_name": "gpt-4o-mini",
                "set_active": True,
                "remark": "来自 LLM_API_KEY / LLM_API_ENDPOINT",
            }
        )
        logger.info("已从环境变量创建 LlmProvider: %s", row.id)
