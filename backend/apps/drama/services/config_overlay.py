# -*- coding: utf-8 -*-
"""运营配置覆盖服务。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.db import transaction

from apps.core.audit import audit_log
from apps.core.exceptions import OPTIMISTIC_LOCK_FAILED, VALIDATION_ERROR, BusinessException
from apps.core.schema_validator import SchemaValidator
from apps.drama.models import DramaAuditEvent, DramaConfigRevision
from apps.drama.services.config_resolver import ConfigResolver
from apps.drama.services.skills_loader import get_skills_loader


class ConfigOverlayService:
    """后台 ops overlay 读写与回滚。"""

    SCHEMA_PATH = "ops-config-overlay.v1.schema.json"

    def __init__(self) -> None:
        self.loader = get_skills_loader()
        self.validator = SchemaValidator()
        self.resolver = ConfigResolver(self.loader.config_policy)

    def get_current(self) -> dict[str, Any] | None:
        latest = DramaConfigRevision.objects.order_by("-revision").first()
        return latest.overlay if latest else None

    def get_current_or_empty(self) -> dict[str, Any]:
        """后台读取：无 revision 时返回可编辑的空壳，避免前端白屏。"""
        current = self.get_current()
        if current:
            return current
        return self.build_empty_overlay()

    def build_empty_overlay(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "schema_version": "ops-config-overlay.v1",
            "tenant_id": "default",
            "skills_version": self.loader.bundle_version,
            "overrides": {},
            "audit": {
                "revision": 0,
                "updated_by": "system",
                "updated_at": now,
                "change_reason": "尚未创建覆盖，当前使用技能仓库默认值",
            },
        }

    def get_revision(self, revision: int) -> DramaConfigRevision:
        return DramaConfigRevision.objects.get(revision=revision)

    @transaction.atomic
    def put_overlay(
        self,
        payload: dict[str, Any],
        *,
        expected_revision: int,
        actor: str,
    ) -> dict[str, Any]:
        latest = DramaConfigRevision.objects.order_by("-revision").first()
        current_revision = latest.revision if latest else 0
        if current_revision != expected_revision:
            raise BusinessException(
                OPTIMISTIC_LOCK_FAILED,
                f"配置版本冲突，期望 {expected_revision}，实际 {current_revision}",
                http_status=409,
            )

        now = datetime.now(timezone.utc).isoformat()
        audit = dict(payload.get("audit", {}))
        audit["revision"] = current_revision + 1
        audit["updated_at"] = now
        audit["updated_by"] = actor
        if not str(audit.get("change_reason", "")).strip():
            raise BusinessException(
                VALIDATION_ERROR,
                "必须填写修改原因",
                http_status=400,
            )
        payload = dict(payload)
        payload["audit"] = audit

        # 先写入服务端 revision，再做 schema 校验（允许首存从 revision=0 起步）
        self.validator.validate_file(payload, self.SCHEMA_PATH)
        seeds = self._load_seed_files()
        self.resolver.apply_overlay(seeds, payload)

        DramaConfigRevision.objects.create(
            revision=current_revision + 1,
            overlay=payload,
            updated_by=actor,
            change_reason=audit.get("change_reason", ""),
        )
        DramaAuditEvent.objects.create(
            actor=actor,
            action="config.updated",
            detail={"revision": current_revision + 1},
        )
        audit_log("config.updated", actor=actor, detail={"revision": current_revision + 1})
        return payload

    @transaction.atomic
    def rollback(
        self,
        *,
        target_revision: int,
        change_reason: str,
        actor: str,
    ) -> dict[str, Any]:
        source = self.get_revision(target_revision)
        latest = DramaConfigRevision.objects.order_by("-revision").first()
        new_revision = (latest.revision if latest else 0) + 1
        now = datetime.now(timezone.utc).isoformat()
        overlay = dict(source.overlay)
        audit = dict(overlay.get("audit", {}))
        audit["revision"] = new_revision
        audit["updated_at"] = now
        audit["updated_by"] = actor
        audit["change_reason"] = change_reason
        overlay["audit"] = audit

        self.validator.validate_file(overlay, self.SCHEMA_PATH)
        seeds = self._load_seed_files()
        self.resolver.apply_overlay(seeds, overlay)

        DramaConfigRevision.objects.create(
            revision=new_revision,
            overlay=overlay,
            updated_by=actor,
            change_reason=change_reason,
        )
        DramaAuditEvent.objects.create(
            actor=actor,
            action="config.rollback",
            detail={"from": latest.revision if latest else 0, "to": target_revision},
        )
        return overlay

    def _load_seed_files(self) -> dict[str, dict[str, Any]]:
        policy = self.loader.config_policy
        seeds: dict[str, dict[str, Any]] = {}
        for file_path in (policy.get("overlay_files") or {}):
            seeds[file_path] = self.loader.load_seed_yaml(file_path)
        return seeds
