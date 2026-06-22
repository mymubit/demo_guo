# -*- coding: utf-8 -*-
"""Tier 规则条目 — 拆分、CRUD、引用统计。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from apps.skill.models import SkillRuleConfig, SkillRuleItem
from apps.skill.skills.admin_service import SkillRuleConfigService
from apps.skill.skills.rule_item_flatten import flatten_config

logger = logging.getLogger(__name__)


class SkillRuleItemService:
    @staticmethod
    def serialize(row: SkillRuleItem) -> Dict[str, Any]:
        return {
            "id": str(row.id),
            "rule_key": row.rule_key,
            "config_id": str(row.config_id) if row.config_id else None,
            "tier": row.tier,
            "scope_type": row.scope_type,
            "scope_key": row.scope_key,
            "section": row.section,
            "section_label": SkillRuleConfigService._section_label(row.tier, row.section),
            "item_type": row.item_type,
            "title": row.title,
            "body": row.body,
            "payload": row.payload,
            "priority": row.priority,
            "sort_order": row.sort_order,
            "version_tag": row.version_tag,
            "status": row.status,
            "source": row.source,
            "note": row.note,
            "apply_count": row.apply_count,
            "last_applied_at": row.last_applied_at.isoformat() if row.last_applied_at else None,
            "approved_by": row.approved_by,
            "approved_at": row.approved_at.isoformat() if row.approved_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }

    @classmethod
    def list_items(
        cls,
        *,
        tier: Optional[int] = None,
        status: Optional[str] = None,
        scope_type: Optional[str] = None,
        section: Optional[str] = None,
        item_type: Optional[str] = None,
        exclude_meta: bool = True,
        q: str = "",
        limit: int = 500,
        offset: int = 0,
    ) -> Dict[str, Any]:
        qs = SkillRuleItem.objects.all().order_by(
            "tier", "scope_type", "scope_key", "section", "sort_order", "priority", "-created_at"
        )
        if tier is not None:
            qs = qs.filter(tier=tier)
        if status:
            qs = qs.filter(status=status)
        if scope_type:
            qs = qs.filter(scope_type=scope_type)
        if section:
            qs = qs.filter(section=section)
        if item_type:
            qs = qs.filter(item_type=item_type)
        if exclude_meta:
            qs = qs.exclude(item_type=SkillRuleItem.TYPE_META)
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(body__icontains=q)
                | Q(rule_key__icontains=q)
                | Q(section__icontains=q)
            )
        total = qs.count()
        rows = qs[offset : offset + max(1, min(limit, 1000))]
        return {
            "items": [cls.serialize(row) for row in rows],
            "total": total,
            "summary": cls.summary(),
        }

    @classmethod
    def summary(cls) -> Dict[str, Any]:
        from django.db.models import Count, Sum

        agg = SkillRuleItem.objects.values("tier", "status").annotate(count=Count("id"))
        by_tier: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for row in agg:
            by_tier[str(row["tier"])] = by_tier.get(str(row["tier"]), 0) + row["count"]
            by_status[row["status"]] = by_status.get(row["status"], 0) + row["count"]
        total_apply = SkillRuleItem.objects.aggregate(total=Sum("apply_count")).get("total") or 0
        return {
            "by_tier": by_tier,
            "by_status": by_status,
            "total_apply_count": int(total_apply),
            "total_items": SkillRuleItem.objects.count(),
        }

    @classmethod
    def get_item(cls, item_id: str) -> Optional[Dict[str, Any]]:
        row = SkillRuleItem.objects.filter(pk=item_id).first()
        return cls.serialize(row) if row else None

    @classmethod
    def save_item(
        cls,
        *,
        item_id: Optional[str] = None,
        rule_key: str,
        tier: int,
        scope_type: str,
        scope_key: str = "",
        section: str,
        title: str,
        body: str,
        item_type: str = SkillRuleItem.TYPE_RULE,
        payload: Optional[Dict[str, Any]] = None,
        priority: int = 100,
        sort_order: int = 0,
        version_tag: str = "v5.0.0",
        status: str = SkillRuleConfig.STATUS_DRAFT,
        note: str = "",
        config_id: Optional[str] = None,
    ) -> SkillRuleItem:
        if not rule_key.strip():
            raise ValueError("rule_key 不能为空")
        if not title.strip():
            raise ValueError("title 不能为空")
        if not body.strip():
            raise ValueError("body 不能为空")

        defaults = {
            "rule_key": rule_key.strip(),
            "tier": tier,
            "scope_type": scope_type,
            "scope_key": scope_key or "",
            "section": section,
            "item_type": item_type,
            "title": title.strip()[:512],
            "body": body,
            "payload": payload or {},
            "priority": priority,
            "sort_order": sort_order,
            "version_tag": version_tag,
            "status": status,
            "note": note,
            "source": SkillRuleConfig.SOURCE_ADMIN,
        }
        if config_id:
            defaults["config_id"] = config_id

        if item_id:
            row = SkillRuleItem.objects.filter(pk=item_id).first()
            if not row:
                raise ValueError("规则条目不存在")
            for key, val in defaults.items():
                setattr(row, key, val)
            row.save()
            return row

        return SkillRuleItem.objects.create(**defaults)

    @classmethod
    def approve_item(cls, item_id: str, *, approved_by: str = "admin") -> SkillRuleItem:
        row = SkillRuleItem.objects.filter(pk=item_id, status=SkillRuleConfig.STATUS_DRAFT).first()
        if not row:
            raise ValueError("仅草稿状态可批准")
        row.approve(approved_by=approved_by)
        return row

    @classmethod
    def archive_item(cls, item_id: str) -> None:
        updated = SkillRuleItem.objects.filter(pk=item_id).exclude(
            status=SkillRuleConfig.STATUS_ARCHIVED
        ).update(status=SkillRuleConfig.STATUS_ARCHIVED)
        if not updated:
            raise ValueError("规则条目不存在或已归档")

    @classmethod
    @transaction.atomic
    def flatten_from_configs(cls, *, overwrite: bool = False, as_draft: bool = True) -> Dict[str, int]:
        SkillRuleConfigService.ensure_defaults()
        configs = SkillRuleConfig.objects.exclude(section__in=("tier_full",)).filter(
            status=SkillRuleConfig.STATUS_ACTIVE,
        )
        archived = 0
        if overwrite:
            archived = SkillRuleItem.objects.filter(status=SkillRuleConfig.STATUS_ACTIVE).update(
                status=SkillRuleConfig.STATUS_ARCHIVED
            )

        created = 0
        skipped = 0
        target_status = SkillRuleConfig.STATUS_DRAFT if as_draft else SkillRuleConfig.STATUS_ACTIVE
        for config in configs:
            drafts = flatten_config(config)
            if not drafts:
                continue
            for draft in drafts:
                rule_key = draft["rule_key"]
                exists = SkillRuleItem.objects.filter(
                    rule_key=rule_key,
                    status__in=[SkillRuleConfig.STATUS_ACTIVE, SkillRuleConfig.STATUS_DRAFT],
                ).exists()
                if exists and not overwrite:
                    skipped += 1
                    continue
                SkillRuleItem.objects.create(
                    config=config,
                    rule_key=rule_key,
                    tier=config.tier,
                    scope_type=config.scope_type,
                    scope_key=config.scope_key,
                    section=config.section,
                    item_type=draft.get("item_type", SkillRuleItem.TYPE_RULE),
                    title=str(draft.get("title") or rule_key)[:512],
                    body=str(draft.get("body") or ""),
                    payload=draft.get("payload") or {},
                    priority=100,
                    sort_order=int(draft.get("sort_order") or 0),
                    version_tag=config.version_tag,
                    status=target_status,
                    source=config.source,
                    note=config.note or f"从配置包 {config.section} 拆分",
                )
                created += 1
        return {
            "created": created,
            "skipped": skipped,
            "archived": archived,
            "configs": configs.count(),
        }

    @classmethod
    def ensure_items(cls) -> Dict[str, int]:
        if SkillRuleItem.objects.exists():
            return {"created": 0, "skipped": 0, "configs": 0, "archived": 0}
        return cls.flatten_from_configs(overwrite=False)

    @classmethod
    def record_apply(cls, item_ids: List[str]) -> None:
        if not item_ids:
            return
        now = timezone.now()
        SkillRuleItem.objects.filter(pk__in=item_ids).update(
            apply_count=F("apply_count") + 1,
            last_applied_at=now,
        )
