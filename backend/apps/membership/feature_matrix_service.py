# -*- coding: utf-8 -*-
"""会员权益矩阵 — DB 优先，代码默认值兜底。"""
from __future__ import annotations

from typing import Any, Dict, List

from .feature_matrix import FREE_TIER_MATRIX
from .models import MembershipFeatureMatrixItem


class FeatureMatrixService:
    @staticmethod
    def resolve_matrix() -> List[Dict[str, Any]]:
        rows = MembershipFeatureMatrixItem.objects.filter(is_active=True).order_by(
            "sort_order", "feature_key"
        )
        if rows.exists():
            return [FeatureMatrixService._row_to_item(r) for r in rows]
        return list(FREE_TIER_MATRIX)

    @staticmethod
    def list_admin_items() -> list:
        rows = {
            r.feature_key: r
            for r in MembershipFeatureMatrixItem.objects.all().order_by("sort_order", "feature_key")
        }
        keys = sorted(set(FREE_TIER_MATRIX_KEY_SET()) | set(rows.keys()))
        items = []
        for idx, key in enumerate(keys):
            row = rows.get(key)
            defaults = FREE_TIER_MATRIX_BY_KEY().get(key, {})
            items.append(
                {
                    "id": str(row.id) if row else None,
                    "feature_key": key,
                    "label": row.label if row else defaults.get("label", key),
                    "free": row.free if row else defaults.get("free", False),
                    "member": row.member if row else defaults.get("member", True),
                    "coming_soon": row.coming_soon if row else defaults.get("coming_soon", False),
                    "member_only": row.member_only if row else defaults.get("member_only", False),
                    "is_active": row.is_active if row else True,
                    "sort_order": row.sort_order if row else (idx + 1) * 10,
                    "source": "db" if row else "default",
                    "updated_at": row.updated_at if row else None,
                }
            )
        return items

    @staticmethod
    def upsert(feature_key: str, data: Dict[str, Any]) -> MembershipFeatureMatrixItem:
        key = (feature_key or "").strip()
        defaults = FREE_TIER_MATRIX_BY_KEY().get(key, {})
        row, _ = MembershipFeatureMatrixItem.objects.update_or_create(
            feature_key=key,
            defaults={
                "label": str(data.get("label") or defaults.get("label") or key)[:128],
                "free": bool(data.get("free") if "free" in data else defaults.get("free", False)),
                "member": bool(data.get("member") if "member" in data else defaults.get("member", True)),
                "coming_soon": bool(
                    data.get("coming_soon") if "coming_soon" in data else defaults.get("coming_soon", False)
                ),
                "member_only": bool(
                    data.get("member_only") if "member_only" in data else defaults.get("member_only", False)
                ),
                "is_active": bool(data.get("is_active", True)),
                "sort_order": int(data.get("sort_order") or 0),
            },
        )
        return row

    @staticmethod
    def seed_defaults() -> int:
        created = 0
        for idx, item in enumerate(FREE_TIER_MATRIX):
            _, was_created = MembershipFeatureMatrixItem.objects.update_or_create(
                feature_key=item["key"],
                defaults={
                    "label": item["label"],
                    "free": item.get("free", False),
                    "member": item.get("member", True),
                    "coming_soon": item.get("coming_soon", False),
                    "member_only": item.get("member_only", False),
                    "is_active": True,
                    "sort_order": (idx + 1) * 10,
                },
            )
            if was_created:
                created += 1
        return created

    @staticmethod
    def _row_to_item(row: MembershipFeatureMatrixItem) -> Dict[str, Any]:
        item = {
            "key": row.feature_key,
            "label": row.label,
            "free": row.free,
            "member": row.member,
        }
        if row.coming_soon:
            item["coming_soon"] = True
        if row.member_only:
            item["member_only"] = True
        return item


def FREE_TIER_MATRIX_BY_KEY() -> Dict[str, Dict[str, Any]]:
    return {item["key"]: item for item in FREE_TIER_MATRIX}


def FREE_TIER_MATRIX_KEY_SET():
    return {item["key"] for item in FREE_TIER_MATRIX}
