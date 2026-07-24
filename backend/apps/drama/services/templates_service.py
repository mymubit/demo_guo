# -*- coding: utf-8 -*-
"""V3 模板库：内置 preset + 自定义模板 CRUD / 建项种子。"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from apps.core.exceptions import NOT_FOUND, VALIDATION_ERROR, BusinessException
from apps.drama.models import V3ProjectTemplate
from apps.drama.services.skills_loader import get_skills_loader


def list_builtin_templates() -> list[dict[str, Any]]:
    """从 theme-matrix.yaml#preset_templates 投影内置模板。"""
    raw = get_skills_loader().load_seed_yaml("foundation/theme-matrix.yaml")
    items: list[dict[str, Any]] = []
    for item in raw.get("preset_templates") or []:
        theme_code = (item.get("theme_code") or "").strip()
        if not theme_code:
            continue
        items.append(
            {
                "theme_code": theme_code,
                "label_zh": item.get("label_zh") or item.get("label") or theme_code,
                "dims": dict(item.get("dims") or {}),
                "kind": "builtin",
            }
        )
    return items


def _serialize_custom(obj: V3ProjectTemplate) -> dict[str, Any]:
    return {
        "id": str(obj.id),
        "name": obj.name,
        "theme_code": obj.theme_code,
        "label_zh": obj.label_zh,
        "dims": obj.dims or {},
        "description": obj.description or "",
        "created_by": (
            getattr(obj.created_by, "username", None) if obj.created_by_id else None
        ),
        "created_at": obj.created_at.isoformat().replace("+00:00", "Z")
        if obj.created_at
        else None,
        "updated_at": obj.updated_at.isoformat().replace("+00:00", "Z")
        if obj.updated_at
        else None,
        "kind": "custom",
    }


def list_custom_templates() -> list[dict[str, Any]]:
    qs = V3ProjectTemplate.objects.select_related("created_by").order_by("-updated_at")
    return [_serialize_custom(obj) for obj in qs]


def list_templates() -> dict[str, list[dict[str, Any]]]:
    return {
        "builtin": list_builtin_templates(),
        "custom": list_custom_templates(),
    }


def create_custom_template(*, data: dict[str, Any], user) -> dict[str, Any]:
    obj = V3ProjectTemplate.objects.create(
        name=data["name"],
        theme_code=data["theme_code"],
        label_zh=data["label_zh"],
        dims=data.get("dims") or {},
        description=data.get("description") or "",
        created_by=user,
    )
    return _serialize_custom(obj)


def update_custom_template(
    *, template_id: UUID, data: dict[str, Any]
) -> dict[str, Any]:
    try:
        obj = V3ProjectTemplate.objects.select_related("created_by").get(id=template_id)
    except V3ProjectTemplate.DoesNotExist as exc:
        raise BusinessException(NOT_FOUND, "自定义模板不存在", http_status=404) from exc
    for field in ("name", "theme_code", "label_zh", "dims", "description"):
        if field in data:
            setattr(obj, field, data[field])
    obj.save()
    return _serialize_custom(obj)


def delete_custom_template(*, template_id: UUID) -> None:
    deleted, _ = V3ProjectTemplate.objects.filter(id=template_id).delete()
    if not deleted:
        raise BusinessException(NOT_FOUND, "自定义模板不存在", http_status=404)


def resolve_template_seed(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    从 create_project payload 解析 template_seed。
    支持 template_id（自定义）或 theme_code（内置）；二者互斥。
    """
    data = payload or {}
    template_id = data.get("template_id")
    theme_code = (data.get("theme_code") or "").strip()
    if template_id and theme_code:
        raise BusinessException(
            VALIDATION_ERROR,
            "template_id 与 theme_code 不能同时提供",
            http_status=400,
        )
    if template_id:
        try:
            obj = V3ProjectTemplate.objects.get(id=template_id)
        except (V3ProjectTemplate.DoesNotExist, ValueError, TypeError) as exc:
            raise BusinessException(
                VALIDATION_ERROR, "自定义模板不存在", http_status=400
            ) from exc
        return {
            "source": "custom",
            "template_id": str(obj.id),
            "name": obj.name,
            "theme_code": obj.theme_code,
            "label_zh": obj.label_zh,
            "dims": dict(obj.dims or {}),
            "description": obj.description or "",
        }
    if theme_code:
        for item in list_builtin_templates():
            if item["theme_code"] == theme_code:
                return {
                    "source": "builtin",
                    "template_id": None,
                    "name": None,
                    "theme_code": item["theme_code"],
                    "label_zh": item["label_zh"],
                    "dims": dict(item.get("dims") or {}),
                    "description": "",
                }
        raise BusinessException(
            VALIDATION_ERROR,
            f"未知内置 theme_code: {theme_code}",
            http_status=400,
        )
    return None
