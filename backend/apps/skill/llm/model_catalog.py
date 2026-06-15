# -*- coding: utf-8 -*-
"""大模型目录（DB）读写 — Admin 可维护。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.db import transaction

from apps.skill.config.bootstrap.llm_model_catalog import CATALOG_SEED
from apps.skill.models import LlmModelCatalog, LlmProvider
from apps.skill.config.portal.skill_settings import SkillConfigService

logger = logging.getLogger(__name__)


class LlmCatalogError(Exception):
    pass


class LlmCatalogService:
    @staticmethod
    def normalize_base_url(endpoint: str) -> str:
        return SkillConfigService._normalize_llm_base_url(endpoint or "")

    @classmethod
    def list_catalog(cls, *, enabled_only: bool = False) -> List[LlmModelCatalog]:
        qs = LlmModelCatalog.objects.all()
        if enabled_only:
            qs = qs.filter(is_enabled=True)
        return list(qs.order_by("sort_order", "vendor", "name"))

    @classmethod
    def get_by_id(cls, catalog_id) -> Optional[LlmModelCatalog]:
        try:
            return LlmModelCatalog.objects.get(pk=catalog_id)
        except LlmModelCatalog.DoesNotExist:
            return None

    @classmethod
    def get_by_preset_key(cls, preset_key: str) -> Optional[LlmModelCatalog]:
        try:
            return LlmModelCatalog.objects.get(preset_key=preset_key)
        except LlmModelCatalog.DoesNotExist:
            return None

    @classmethod
    def serialize(cls, row: LlmModelCatalog, *, configured: bool = False) -> Dict[str, Any]:
        return {
            "id": str(row.id),
            "key": row.preset_key,
            "preset_key": row.preset_key,
            "name": row.name,
            "vendor": row.vendor,
            "vendor_label": row.vendor_label or row.vendor,
            "base_url": row.base_url,
            "model_name": row.model_name,
            "temperature": row.temperature,
            "max_tokens": row.max_tokens,
            "context_window_input": row.context_window_input,
            "context_window_output": row.context_window_output,
            "tool_call_rounds": row.tool_call_rounds,
            "supports_multimodal": row.supports_multimodal,
            "api_key_hint": row.api_key_hint,
            "api_key_url": row.api_key_url,
            "remark": row.remark,
            "input_price_per_million": str(row.input_price_per_million)
            if row.input_price_per_million is not None
            else None,
            "output_price_per_million": str(row.output_price_per_million)
            if row.output_price_per_million is not None
            else None,
            "is_enabled": row.is_enabled,
            "sort_order": row.sort_order,
            "configured": configured,
            "updated_at": row.updated_at,
        }

    @classmethod
    def list_presets_with_status(cls) -> List[Dict[str, Any]]:
        pairs = {
            (cls.normalize_base_url(row.base_url), row.model_name)
            for row in LlmProvider.objects.all()
        }
        out: List[Dict[str, Any]] = []
        for row in cls.list_catalog(enabled_only=True):
            base = cls.normalize_base_url(row.base_url)
            configured = (base, row.model_name) in pairs
            out.append(cls.serialize(row, configured=configured))
        return out

    @classmethod
    def list_vendors_grouped(cls) -> List[Dict[str, Any]]:
        groups: Dict[str, Dict[str, Any]] = {}
        for preset in cls.list_presets_with_status():
            vendor = preset["vendor"]
            if vendor not in groups:
                groups[vendor] = {
                    "vendor": vendor,
                    "vendor_label": preset["vendor_label"],
                    "api_key_url": preset.get("api_key_url") or "",
                    "models": [],
                }
            groups[vendor]["models"].append(preset)
        return sorted(groups.values(), key=lambda g: (g["models"][0].get("sort_order", 0), g["vendor"]))

    @classmethod
    @transaction.atomic
    def ensure_seed_catalog(cls) -> int:
        """写入缺失目录项，并将种子中的元数据同步到已有 preset（不删改 Admin 自定义项）。"""
        created = 0
        updated = 0
        sync_fields = (
            "name",
            "vendor",
            "vendor_label",
            "base_url",
            "temperature",
            "max_tokens",
            "context_window_input",
            "context_window_output",
            "tool_call_rounds",
            "supports_multimodal",
            "api_key_hint",
            "api_key_url",
            "remark",
            "sort_order",
            "input_price_per_million",
            "output_price_per_million",
        )
        for item in CATALOG_SEED:
            row = LlmModelCatalog.objects.filter(preset_key=item["preset_key"]).first()
            if row is None:
                row = LlmModelCatalog(preset_key=item["preset_key"], is_enabled=True)
                cls._apply_seed_item(row, item, include_model_name=True)
                row.save()
                created += 1
                continue
            before = {f: getattr(row, f) for f in sync_fields}
            cls._apply_seed_item(row, item, include_model_name=False)
            # 已有 Admin 填写的单价不覆盖
            if row.pk:
                if before.get("input_price_per_million") is not None:
                    row.input_price_per_million = before["input_price_per_million"]
                if before.get("output_price_per_million") is not None:
                    row.output_price_per_million = before["output_price_per_million"]
            seed_model = str(item.get("model_name") or "").strip()
            force_sync = bool(item.get("force_model_name_sync"))
            if seed_model and (
                force_sync
                or str(row.model_name or "").strip().lower() in {"ep-xxx", "ep-xxxxxxxxx", ""}
            ):
                row.model_name = seed_model
            after = {f: getattr(row, f) for f in sync_fields}
            if row.model_name != before.get("model_name"):
                after = {**after, "model_name": row.model_name}
            if before != after:
                row.save()
                updated += 1
        if created or updated:
            logger.info("大模型目录种子：新增 %d 条，更新 %d 条", created, updated)
        return created + updated

    @classmethod
    @transaction.atomic
    def sync_official_pricing(cls, *, preset_keys: Optional[List[str]] = None) -> int:
        """按种子中的官方单价强制写入目录（覆盖 Admin 已填价格）。"""
        seed_by_key = {item["preset_key"]: item for item in CATALOG_SEED}
        keys = preset_keys or list(seed_by_key.keys())
        updated = 0
        for key in keys:
            item = seed_by_key.get(key)
            if not item:
                logger.warning("sync_official_pricing: 未知 preset_key=%s", key)
                continue
            row = LlmModelCatalog.objects.filter(preset_key=key).first()
            if row is None:
                row = LlmModelCatalog(preset_key=key, is_enabled=True)
                cls._apply_seed_item(row, item, include_model_name=True)
                row.save()
                updated += 1
                continue
            inp = item.get("input_price_per_million")
            out = item.get("output_price_per_million")
            if inp is None and out is None:
                continue
            changed = False
            if inp is not None and str(row.input_price_per_million) != str(inp):
                row.input_price_per_million = inp
                changed = True
            if out is not None and str(row.output_price_per_million) != str(out):
                row.output_price_per_million = out
                changed = True
            if changed:
                row.save(update_fields=["input_price_per_million", "output_price_per_million", "updated_at"])
                updated += 1
        if updated:
            logger.info("大模型官方单价同步：更新 %d 条", updated)
        return updated

    @classmethod
    def _apply_seed_item(
        cls, row: LlmModelCatalog, item: Dict[str, Any], *, include_model_name: bool = True
    ) -> None:
        row.name = item["name"]
        row.vendor = item["vendor"]
        row.vendor_label = item.get("vendor_label", "")
        row.base_url = cls.normalize_base_url(item["base_url"])
        if include_model_name:
            row.model_name = item["model_name"]
        row.temperature = float(item.get("temperature", 0.7))
        row.max_tokens = max(256, int(item.get("max_tokens", 8192)))
        row.context_window_input = item.get("context_window_input")
        row.context_window_output = item.get("context_window_output")
        row.tool_call_rounds = item.get("tool_call_rounds")
        row.supports_multimodal = bool(item.get("supports_multimodal", False))
        row.api_key_hint = str(item.get("api_key_hint") or "")[:255]
        row.api_key_url = str(item.get("api_key_url") or "")[:512]
        row.remark = str(item.get("remark") or "")[:512]
        row.input_price_per_million = item.get("input_price_per_million")
        row.output_price_per_million = item.get("output_price_per_million")
        row.sort_order = int(item.get("sort_order", 0))
        if row.pk is None:
            row.is_enabled = True

    @classmethod
    @transaction.atomic
    def create_catalog(cls, data: Dict[str, Any]) -> LlmModelCatalog:
        preset_key = str(data.get("preset_key") or data.get("key") or "").strip()
        if not preset_key:
            raise LlmCatalogError("preset_key 不能为空")
        if LlmModelCatalog.objects.filter(preset_key=preset_key).exists():
            raise LlmCatalogError(f"预设键 {preset_key} 已存在")
        row = cls._apply_fields(LlmModelCatalog(preset_key=preset_key), data)
        row.save()
        return row

    @classmethod
    @transaction.atomic
    def update_catalog(cls, catalog_id, data: Dict[str, Any]) -> LlmModelCatalog:
        row = cls.get_by_id(catalog_id)
        if row is None:
            raise LlmCatalogError("目录项不存在")
        if "preset_key" in data or "key" in data:
            new_key = str(data.get("preset_key") or data.get("key") or row.preset_key).strip()
            if new_key != row.preset_key and LlmModelCatalog.objects.filter(preset_key=new_key).exists():
                raise LlmCatalogError(f"预设键 {new_key} 已存在")
            row.preset_key = new_key
        row = cls._apply_fields(row, data)
        row.save()
        return row

    @classmethod
    @transaction.atomic
    def delete_catalog(cls, catalog_id) -> None:
        row = cls.get_by_id(catalog_id)
        if row is None:
            raise LlmCatalogError("目录项不存在")
        if row.providers.exists():
            raise LlmCatalogError("已有接入配置引用此目录，请先删除接入实例")
        row.delete()

    @classmethod
    def _apply_fields(cls, row: LlmModelCatalog, data: Dict[str, Any]) -> LlmModelCatalog:
        if "name" in data:
            row.name = str(data["name"] or row.name).strip()[:100]
        if "vendor" in data:
            row.vendor = str(data["vendor"] or row.vendor).strip()[:64]
        if "vendor_label" in data:
            row.vendor_label = str(data["vendor_label"] or "")[:64]
        if "base_url" in data:
            row.base_url = cls.normalize_base_url(str(data["base_url"] or ""))
        if "model_name" in data:
            row.model_name = str(data["model_name"] or row.model_name).strip()[:128]
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
        if "api_key_hint" in data:
            row.api_key_hint = str(data["api_key_hint"] or "")[:255]
        if "api_key_url" in data:
            row.api_key_url = str(data["api_key_url"] or "")[:512]
        if "remark" in data:
            row.remark = str(data["remark"] or "")[:512]
        if "input_price_per_million" in data:
            val = data["input_price_per_million"]
            row.input_price_per_million = val if val not in (None, "") else None
        if "output_price_per_million" in data:
            val = data["output_price_per_million"]
            row.output_price_per_million = val if val not in (None, "") else None
        if "is_enabled" in data:
            row.is_enabled = bool(data["is_enabled"])
        if "sort_order" in data:
            row.sort_order = int(data["sort_order"] or 0)
        return row

    @classmethod
    def defaults_for_provider(cls, catalog: LlmModelCatalog) -> Dict[str, Any]:
        return {
            "catalog_id": str(catalog.id),
            "name": catalog.name,
            "base_url": catalog.base_url,
            "model_name": catalog.model_name,
            "temperature": catalog.temperature,
            "max_tokens": catalog.max_tokens,
            "context_window_input": catalog.context_window_input,
            "context_window_output": catalog.context_window_output,
            "tool_call_rounds": catalog.tool_call_rounds,
            "supports_multimodal": catalog.supports_multimodal,
            "remark": catalog.remark,
            "sort_order": catalog.sort_order,
        }
