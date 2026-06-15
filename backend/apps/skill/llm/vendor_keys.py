# -*- coding: utf-8 -*-
"""厂商级 LLM API Key（同一 vendor 下多模型共用）。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.db import transaction

from apps.skill.llm.model_catalog import LlmCatalogService
from apps.skill.models import LlmProvider
from apps.skill.config.portal.skill_settings import SkillConfigService
from apps.skill.llm.volcengine_config import infer_volcano_key_type, is_volcano_host, resolve_volcano_base_url

logger = logging.getLogger(__name__)

VENDOR_KEY_PREFIX = "llm.vendor."
VENDOR_KEY_SUFFIX = ".api_key"
VENDOR_VOLCANO_TYPE_SUFFIX = ".volcano_key_type"


def resolve_provider_vendor(row: LlmProvider) -> str:
    if row.catalog_id and row.catalog.vendor:
        return str(row.catalog.vendor).strip()
    if is_volcano_host(row.base_url or ""):
        return "volcengine"
    return ""


class LlmVendorCredentialService:
    @classmethod
    def _config_key(cls, vendor: str, *, volcano_type: bool = False) -> str:
        v = str(vendor or "").strip()
        if volcano_type:
            return f"{VENDOR_KEY_PREFIX}{v}{VENDOR_VOLCANO_TYPE_SUFFIX}"
        return f"{VENDOR_KEY_PREFIX}{v}{VENDOR_KEY_SUFFIX}"

    @classmethod
    def _vendor_label(cls, vendor: str) -> str:
        for row in LlmCatalogService.list_catalog(enabled_only=False):
            if row.vendor == vendor:
                return row.vendor_label or row.vendor
        return vendor

    @classmethod
    def _vendor_api_key_url(cls, vendor: str) -> str:
        for row in LlmCatalogService.list_catalog(enabled_only=False):
            if row.vendor == vendor and row.api_key_url:
                return row.api_key_url
        return ""

    @classmethod
    def list_vendors(cls) -> List[str]:
        vendors = set()
        for row in LlmCatalogService.list_catalog(enabled_only=False):
            if row.vendor:
                vendors.add(row.vendor)
        for row in LlmProvider.objects.select_related("catalog").all():
            vendor = resolve_provider_vendor(row)
            if vendor:
                vendors.add(vendor)
        return sorted(vendors)

    @classmethod
    def providers_for_vendor(cls, vendor: str) -> List[LlmProvider]:
        vendor = str(vendor or "").strip()
        if not vendor:
            return []
        rows = list(LlmProvider.objects.select_related("catalog").all())
        return [row for row in rows if resolve_provider_vendor(row) == vendor]

    @classmethod
    def get_api_key(cls, vendor: str) -> str:
        vendor = str(vendor or "").strip()
        if not vendor:
            return ""
        stored = SkillConfigService.get(cls._config_key(vendor), "")
        if stored:
            return stored
        for row in cls.providers_for_vendor(vendor):
            if row.api_key_set:
                key = row.get_api_key() or ""
                if key:
                    return key
        return ""

    @classmethod
    def get_volcano_key_type(cls, vendor: str) -> str:
        if vendor != "volcengine":
            return ""
        stored = SkillConfigService.get(cls._config_key(vendor, volcano_type=True), "")
        if stored in {"payg", "coding_plan"}:
            return stored
        for row in cls.providers_for_vendor(vendor):
            key_type = row.volcano_key_type or infer_volcano_key_type(row.base_url)
            if key_type:
                return key_type
        return "payg"

    @classmethod
    def api_key_set(cls, vendor: str) -> bool:
        return bool(cls.get_api_key(vendor))

    @classmethod
    def serialize_vendor(cls, vendor: str, *, include_api_key: bool = False) -> Dict[str, Any]:
        providers = cls.providers_for_vendor(vendor)
        return {
            "vendor": vendor,
            "vendor_label": cls._vendor_label(vendor),
            "api_key_url": cls._vendor_api_key_url(vendor),
            "api_key_set": cls.api_key_set(vendor),
            "api_key": cls.get_api_key(vendor) if include_api_key else "",
            "volcano_key_type": cls.get_volcano_key_type(vendor) if vendor == "volcengine" else "",
            "provider_count": len(providers),
        }

    @classmethod
    def list_for_admin(cls, *, include_api_key: bool = False) -> List[Dict[str, Any]]:
        return [cls.serialize_vendor(v, include_api_key=include_api_key) for v in cls.list_vendors()]

    @classmethod
    @transaction.atomic
    def set_vendor_credential(
        cls,
        vendor: str,
        *,
        api_key: Optional[str] = None,
        volcano_key_type: Optional[str] = None,
        sync_providers: bool = True,
    ) -> Dict[str, Any]:
        vendor = str(vendor or "").strip()
        if not vendor:
            raise ValueError("vendor 不能为空")

        if api_key is not None:
            val = str(api_key or "").strip()
            if val and val != "******":
                SkillConfigService.set(
                    cls._config_key(vendor),
                    val,
                    description=f"{cls._vendor_label(vendor)} 共用 API Key",
                )

        if vendor == "volcengine" and volcano_key_type is not None:
            key_type = str(volcano_key_type or "payg").strip()[:32]
            if key_type not in {"payg", "coding_plan"}:
                key_type = "payg"
            SkillConfigService.set(
                cls._config_key(vendor, volcano_type=True),
                key_type,
                description="火山方舟 Key 类型（payg / coding_plan）",
            )

        resolved_key = cls.get_api_key(vendor)
        resolved_type = cls.get_volcano_key_type(vendor) if vendor == "volcengine" else ""

        if sync_providers and resolved_key:
            from apps.skill.llm.providers import LlmProviderService

            for row in cls.providers_for_vendor(vendor):
                row.set_api_key(resolved_key)
                if vendor == "volcengine" and resolved_type:
                    row.volcano_key_type = resolved_type
                    row.base_url = LlmProviderService.normalize_base_url(
                        resolve_volcano_base_url(resolved_type)
                    )
                row.save()

        return cls.serialize_vendor(vendor, include_api_key=True)

    @classmethod
    def inherit_api_key_for_provider(cls, row: LlmProvider) -> bool:
        """新建模型时继承厂商 Key。返回是否写入成功。"""
        vendor = resolve_provider_vendor(row)
        if not vendor or row.api_key_set:
            return False
        api_key = cls.get_api_key(vendor)
        if not api_key:
            return False
        row.set_api_key(api_key)
        if vendor == "volcengine":
            key_type = cls.get_volcano_key_type(vendor)
            if key_type:
                row.volcano_key_type = key_type
                from apps.skill.llm.providers import LlmProviderService

                row.base_url = LlmProviderService.normalize_base_url(
                    resolve_volcano_base_url(key_type)
                )
        return True
