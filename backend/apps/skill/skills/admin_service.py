# -*- coding: utf-8 -*-
"""技能规则库后台读写 — Tier1–4，DB 优先，JSON 兜底。"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.db.models import Q

from apps.skill.models import SkillRuleConfig
from .loader import _get_rules_root

logger = logging.getLogger(__name__)

TIER1_SECTION = "tier_full"
TIER4_SECTION = "tier_full"


class SkillRuleConfigService:
    @staticmethod
    def clear_rule_caches() -> None:
        try:
            from apps.skill.skills.loader import _HOT_RELOAD_CACHE, _HOT_RELOAD_MTIME, _PERMANENT_CACHE

            _PERMANENT_CACHE.pop("tier1-iron-rules.json", None)
            _PERMANENT_CACHE.pop("tier4-compliance-rules.json", None)
            _HOT_RELOAD_CACHE.clear()
            _HOT_RELOAD_MTIME.clear()
        except Exception as exc:  # noqa: BLE001
            logger.debug("skill rule cache clear failed: %s", exc)

    @staticmethod
    def serialize(row: SkillRuleConfig) -> Dict[str, Any]:
        return {
            "id": str(row.id),
            "tier": row.tier,
            "scope_type": row.scope_type,
            "scope_key": row.scope_key,
            "section": row.section,
            "content": row.content,
            "version_tag": row.version_tag,
            "status": row.status,
            "source": row.source,
            "note": row.note,
            "approved_by": row.approved_by,
            "approved_at": row.approved_at.isoformat() if row.approved_at else None,
            "trigger_score_avg": row.trigger_score_avg,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "label": str(row),
        }

    @classmethod
    def list_rules(
        cls,
        *,
        tier: Optional[int] = None,
        status: Optional[str] = None,
        scope_type: Optional[str] = None,
        q: str = "",
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        qs = SkillRuleConfig.objects.all().order_by("tier", "scope_type", "scope_key", "section", "-updated_at")
        if tier is not None:
            qs = qs.filter(tier=tier)
        if status:
            qs = qs.filter(status=status)
        if scope_type:
            qs = qs.filter(scope_type=scope_type)
        if q:
            qs = qs.filter(
                Q(scope_key__icontains=q) | Q(section__icontains=q) | Q(note__icontains=q)
            )
        return [cls.serialize(row) for row in qs[: max(1, min(limit, 500))]]

    @classmethod
    def get_rule(cls, rule_id: str) -> Optional[Dict[str, Any]]:
        row = SkillRuleConfig.objects.filter(pk=rule_id).first()
        return cls.serialize(row) if row else None

    @classmethod
    def save_rule(
        cls,
        *,
        rule_id: Optional[str] = None,
        tier: int,
        scope_type: str,
        scope_key: str = "",
        section: str,
        content: Any,
        version_tag: str = "v5.0.0",
        status: str = SkillRuleConfig.STATUS_DRAFT,
        note: str = "",
        approved_by: str = "",
    ) -> SkillRuleConfig:
        if not isinstance(content, (dict, list)):
            raise ValueError("content 必须是 JSON 对象或数组")

        defaults = {
            "tier": tier,
            "scope_type": scope_type,
            "scope_key": scope_key or "",
            "section": section,
            "content": content,
            "version_tag": version_tag[:32],
            "status": status,
            "source": SkillRuleConfig.SOURCE_ADMIN,
            "note": note or "",
        }
        if rule_id:
            row = SkillRuleConfig.objects.filter(pk=rule_id).first()
            if not row:
                raise ValueError("规则不存在")
            for key, val in defaults.items():
                setattr(row, key, val)
            row.save()
        else:
            row = SkillRuleConfig.objects.create(**defaults)

        if status == SkillRuleConfig.STATUS_ACTIVE:
            row.approve(approved_by=approved_by or "admin")
        cls.clear_rule_caches()
        return row

    @classmethod
    def approve_rule(cls, rule_id: str, *, approved_by: str = "admin") -> SkillRuleConfig:
        row = SkillRuleConfig.objects.filter(pk=rule_id, status=SkillRuleConfig.STATUS_DRAFT).first()
        if not row:
            raise ValueError("仅 draft 状态规则可批准")
        row.approve(approved_by=approved_by)
        cls.clear_rule_caches()
        return row

    @classmethod
    def archive_rule(cls, rule_id: str) -> None:
        updated = SkillRuleConfig.objects.filter(pk=rule_id).exclude(
            status=SkillRuleConfig.STATUS_ARCHIVED
        ).update(status=SkillRuleConfig.STATUS_ARCHIVED)
        if not updated:
            raise ValueError("规则不存在或已归档")
        cls.clear_rule_caches()

    @classmethod
    def _upsert_active(
        cls,
        *,
        tier: int,
        scope_type: str,
        scope_key: str,
        section: str,
        content: dict,
        version_tag: str,
        note: str,
        overwrite: bool,
    ) -> bool:
        existing = SkillRuleConfig.objects.filter(
            tier=tier,
            scope_type=scope_type,
            scope_key=scope_key,
            section=section,
            status=SkillRuleConfig.STATUS_ACTIVE,
        ).first()
        if existing and not overwrite:
            return False
        if existing and overwrite:
            existing.status = SkillRuleConfig.STATUS_ARCHIVED
            existing.save(update_fields=["status", "updated_at"])
        SkillRuleConfig.objects.create(
            tier=tier,
            scope_type=scope_type,
            scope_key=scope_key,
            section=section,
            content=content,
            version_tag=version_tag,
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_FILE,
            note=note,
            approved_by="system_import",
        )
        return True

    @classmethod
    def import_from_files(cls, *, rules_dir: Optional[Path] = None, overwrite: bool = False) -> Dict[str, int]:
        root = rules_dir or _get_rules_root()
        counts = {"tier1": 0, "tier2": 0, "tier3": 0, "tier4": 0}

        tier1_file = root / "tier1-iron-rules.json"
        if tier1_file.is_file():
            data = json.loads(tier1_file.read_text(encoding="utf-8"))
            if cls._upsert_active(
                tier=1,
                scope_type=SkillRuleConfig.SCOPE_GLOBAL,
                scope_key="",
                section=TIER1_SECTION,
                content=data,
                version_tag=(data.get("_meta") or {}).get("version", "v5.0.0"),
                note="从 tier1-iron-rules.json 导入",
                overwrite=overwrite,
            ):
                counts["tier1"] = 1

        tier4_file = root / "tier4-compliance-rules.json"
        if tier4_file.is_file():
            data = json.loads(tier4_file.read_text(encoding="utf-8"))
            if cls._upsert_active(
                tier=4,
                scope_type=SkillRuleConfig.SCOPE_GLOBAL,
                scope_key="",
                section=TIER4_SECTION,
                content=data,
                version_tag=(data.get("_meta") or {}).get("version", "v5.0.0"),
                note="从 tier4-compliance-rules.json 导入",
                overwrite=overwrite,
            ):
                counts["tier4"] = 1

        tier2_file = root / "tier2-genre-rules.json"
        if tier2_file.is_file():
            data = json.loads(tier2_file.read_text(encoding="utf-8"))
            if cls._upsert_active(
                tier=2,
                scope_type=SkillRuleConfig.SCOPE_GLOBAL,
                scope_key="",
                section="tier_full",
                content=data,
                version_tag=(data.get("_meta") or {}).get("version", "v5.0.0"),
                note="从 tier2-genre-rules.json 导入（全量）",
                overwrite=overwrite,
            ):
                counts["tier2"] += 1
            for genre_key, genre_data in (data.get("genres") or {}).items():
                if isinstance(genre_data, dict) and "$ref" in genre_data:
                    continue
                if cls._upsert_active(
                    tier=2,
                    scope_type=SkillRuleConfig.SCOPE_GENRE,
                    scope_key=genre_key,
                    section="genre_full",
                    content=genre_data,
                    version_tag=(data.get("_meta") or {}).get("version", "v5.0.0"),
                    note=f"从 tier2 导入·{genre_data.get('label', genre_key)}",
                    overwrite=overwrite,
                ):
                    counts["tier2"] += 1

        tier3_file = root / "tier3-workflow-rules.json"
        if tier3_file.is_file():
            data = json.loads(tier3_file.read_text(encoding="utf-8"))
            if cls._upsert_active(
                tier=3,
                scope_type=SkillRuleConfig.SCOPE_GLOBAL,
                scope_key="",
                section="tier_full",
                content=data,
                version_tag=(data.get("_meta") or {}).get("version", "v5.0.0"),
                note="从 tier3-workflow-rules.json 导入（全量）",
                overwrite=overwrite,
            ):
                counts["tier3"] += 1
            pipeline = list(data.get("main_pipeline") or []) + list(data.get("optional_nodes") or [])
            for node_def in pipeline:
                node_id = node_def.get("node_id") or ""
                if not node_id:
                    continue
                if cls._upsert_active(
                    tier=3,
                    scope_type=SkillRuleConfig.SCOPE_NODE,
                    scope_key=node_id,
                    section="pipeline_node_full",
                    content=node_def,
                    version_tag=(data.get("_meta") or {}).get("version", "v5.0.0"),
                    note=f"从 tier3 导入·{node_def.get('name', node_id)}",
                    overwrite=overwrite,
                ):
                    counts["tier3"] += 1

        cls.clear_rule_caches()
        return counts

    @classmethod
    def ensure_defaults(cls, *, overwrite: bool = False) -> Dict[str, int]:
        missing_tiers = [
            tier
            for tier in (1, 2, 3, 4)
            if not SkillRuleConfig.objects.filter(
                tier=tier,
                status=SkillRuleConfig.STATUS_ACTIVE,
            ).exists()
        ]
        if not missing_tiers:
            return {}
        try:
            counts = cls.import_from_files(overwrite=overwrite)
            logger.info("[SkillRule] ensure_defaults imported missing tiers %s: %s", missing_tiers, counts)
            return counts
        except Exception as exc:  # noqa: BLE001
            logger.warning("[SkillRule] ensure_defaults failed: %s", exc)
            return {}

    @classmethod
    def summary(cls) -> Dict[str, Any]:
        from django.db.models import Count

        grouped = (
            SkillRuleConfig.objects.values("tier", "status")
            .annotate(count=Count("id"))
            .order_by("tier", "status")
        )
        return {"groups": list(grouped)}
