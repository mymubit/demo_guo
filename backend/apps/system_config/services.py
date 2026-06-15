# -*- coding: utf-8 -*-
"""动态配置读取与写入服务。"""
from __future__ import annotations

from typing import Any

from django.db import transaction

from .cache import (
    CACHE_KEY_PUBLIC_ALL,
    CACHE_TTL,
    clear_all_config_cache,
    get_cache,
    item_cache_key,
    set_cache,
)
from .defaults import DEFAULT_CONFIG_CATEGORIES, DEFAULT_SYSTEM_CONFIGS
from .models import SystemConfigAuditLog, SystemConfigCategory, SystemConfigItem
from .validators import normalize_value, validate_schema


def serialize_public_item(item: SystemConfigItem) -> dict[str, Any]:
    return {
        "key": item.config_key,
        "value": item.effective_value,
        "value_type": item.value_type,
        "category": item.category.code,
        "version": item.version,
        "updated_at": item.updated_at,
    }


class SystemConfigService:
    """配置中心服务门面。"""

    @classmethod
    def get_item(cls, key: str) -> SystemConfigItem | None:
        return (
            SystemConfigItem.objects.select_related("category")
            .filter(config_key=key, deleted_at__isnull=True)
            .first()
        )

    @classmethod
    def get_config(cls, key: str, default_val=None):
        cached = get_cache(item_cache_key(key), None)
        if cached is not None:
            return cached

        item = cls.get_item(key)
        if not item or not item.is_active:
            return default_val

        value = item.effective_value
        set_cache(item_cache_key(key), value, CACHE_TTL)
        return default_val if value is None else value

    @classmethod
    def get_bool(cls, key: str, default_val: bool = False) -> bool:
        return bool(cls.get_config(key, default_val))

    @classmethod
    def get_int(cls, key: str, default_val: int = 0) -> int:
        try:
            return int(cls.get_config(key, default_val))
        except (TypeError, ValueError):
            return default_val

    @classmethod
    def get_float(cls, key: str, default_val: float = 0.0) -> float:
        try:
            return float(cls.get_config(key, default_val))
        except (TypeError, ValueError):
            return default_val

    @classmethod
    def get_json(cls, key: str, default_val=None):
        value = cls.get_config(key, default_val if default_val is not None else {})
        return value if isinstance(value, (dict, list)) else default_val

    @classmethod
    def get_many(cls, keys: list[str], public_only: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        qs = SystemConfigItem.objects.select_related("category").filter(
            config_key__in=keys,
            is_active=True,
            deleted_at__isnull=True,
        )
        if public_only:
            qs = qs.filter(is_public=True, is_sensitive=False)
        by_key = {item.config_key: item for item in qs}
        for key in keys:
            item = by_key.get(key)
            result[key] = item.effective_value if item else None
        return result

    @classmethod
    def public_config_payload(cls) -> dict[str, Any]:
        cached = get_cache(CACHE_KEY_PUBLIC_ALL, None)
        if cached is not None:
            return cached

        rows = (
            SystemConfigItem.objects.select_related("category")
            .filter(is_active=True, is_public=True, is_sensitive=False, deleted_at__isnull=True)
            .order_by("category__sort_order", "config_key")
        )
        items = [serialize_public_item(row) for row in rows]
        payload = {
            "items": items,
            "values": {item["key"]: item["value"] for item in items},
        }
        set_cache(CACHE_KEY_PUBLIC_ALL, payload, CACHE_TTL)
        return payload

    @classmethod
    @transaction.atomic
    def upsert_config(cls, data: dict[str, Any], *, user=None, request=None, overwrite: bool = True):
        category_code = data["category"]
        category, _ = SystemConfigCategory.objects.get_or_create(
            code=category_code,
            defaults={
                "name": data.get("category_name") or category_code,
                "description": data.get("category_description", ""),
                "sort_order": int(data.get("category_sort_order", 0)),
            },
        )
        value_type = data["value_type"]
        value = normalize_value(value_type, data.get("value"))
        default_value = normalize_value(value_type, data.get("default_value", value))
        validation_schema = data.get("validation_schema") or {}
        validate_schema(value, validation_schema)
        validate_schema(default_value, validation_schema)

        obj = cls.get_item(data["config_key"])
        if obj and not overwrite:
            return obj, False

        old_value = obj.effective_value if obj else None
        if obj is None:
            obj = SystemConfigItem(
                category=category,
                config_key=data["config_key"],
                created_by=user if getattr(user, "is_authenticated", False) else None,
            )
            action = SystemConfigAuditLog.Action.CREATE
        else:
            action = SystemConfigAuditLog.Action.UPDATE
            obj.version += 1

        obj.category = category
        obj.config_name = data.get("config_name") or data["config_key"]
        obj.value_type = value_type
        obj.value = value
        obj.default_value = default_value
        obj.description = data.get("description", "")
        obj.validation_schema = validation_schema
        obj.is_active = bool(data.get("is_active", True))
        obj.is_sensitive = bool(data.get("is_sensitive", False))
        obj.is_public = bool(data.get("is_public", False))
        obj.requires_restart = bool(data.get("requires_restart", False))
        obj.deleted_at = None
        if getattr(user, "is_authenticated", False):
            obj.updated_by = user
        obj.save()

        from .audit import write_audit_log
        from .cache import invalidate_config

        invalidate_config(obj.config_key, obj.category.code)
        write_audit_log(
            config=obj,
            config_key=obj.config_key,
            action=action,
            old_value=old_value,
            new_value=obj.effective_value,
            request=request,
            change_reason=data.get("change_reason", ""),
        )
        return obj, action == SystemConfigAuditLog.Action.CREATE

    @classmethod
    def seed_defaults(cls, *, overwrite: bool = False, stdout=None) -> dict[str, int]:
        created_categories = 0
        created_items = 0
        updated_items = 0

        for row in DEFAULT_CONFIG_CATEGORIES:
            _, created = SystemConfigCategory.objects.update_or_create(
                code=row["code"],
                defaults={
                    "name": row["name"],
                    "description": row.get("description", ""),
                    "sort_order": row.get("sort_order", 0),
                    "is_active": row.get("is_active", True),
                },
            )
            if created:
                created_categories += 1

        for row in DEFAULT_SYSTEM_CONFIGS:
            existed = cls.get_item(row["config_key"]) is not None
            obj, created = cls.upsert_config(row, overwrite=overwrite or not existed)
            if created:
                created_items += 1
            elif overwrite:
                updated_items += 1
            if stdout:
                stdout.write(f"seed {obj.config_key}")

        clear_all_config_cache()
        return {
            "created_categories": created_categories,
            "created_items": created_items,
            "updated_items": updated_items,
        }


def get_config(key: str, default_val=None):
    return SystemConfigService.get_config(key, default_val)


def get_bool(key: str, default_val: bool = False) -> bool:
    return SystemConfigService.get_bool(key, default_val)


def get_int(key: str, default_val: int = 0) -> int:
    return SystemConfigService.get_int(key, default_val)


def get_float(key: str, default_val: float = 0.0) -> float:
    return SystemConfigService.get_float(key, default_val)


def get_json(key: str, default_val=None):
    return SystemConfigService.get_json(key, default_val)


def get_many(keys: list[str]) -> dict[str, Any]:
    return SystemConfigService.get_many(keys)
