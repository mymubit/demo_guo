# -*- coding: utf-8 -*-
"""后台：Tier 规则条目 SkillRuleItem。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.skill.models import SkillRuleConfig, SkillRuleItem
from apps.skill.skills.admin_service import SkillRuleConfigService
from apps.skill.skills.rule_item_service import SkillRuleItemService

from apps.console.responses import api_fail, api_ok


class SkillRuleItemListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        tier = request.query_params.get("tier")
        status = request.query_params.get("status")
        scope_type = request.query_params.get("scope_type")
        section = request.query_params.get("section")
        q = request.query_params.get("q") or ""
        try:
            tier_val = int(tier) if tier not in (None, "") else None
        except ValueError:
            return api_fail("tier 参数无效")
        try:
            page = max(1, int(request.query_params.get("page") or 1))
            page_size = max(1, min(int(request.query_params.get("page_size") or 100), 500))
        except ValueError:
            return api_fail("分页参数无效")

        SkillRuleConfigService.ensure_defaults()
        SkillRuleItemService.ensure_items()

        payload = SkillRuleItemService.list_items(
            tier=tier_val,
            status=status or None,
            scope_type=scope_type or None,
            section=section or None,
            q=q,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
        payload["pagination"] = {
            "page": page,
            "page_size": page_size,
            "total": payload.get("total", 0),
            "total_pages": max(1, (payload.get("total", 0) + page_size - 1) // page_size),
        }
        return api_ok(payload)

    def post(self, request):
        data = request.data or {}
        try:
            row = SkillRuleItemService.save_item(
                rule_key=str(data.get("rule_key") or ""),
                tier=int(data.get("tier")),
                scope_type=str(data.get("scope_type") or SkillRuleConfig.SCOPE_GLOBAL),
                scope_key=str(data.get("scope_key") or ""),
                section=str(data.get("section") or "custom"),
                title=str(data.get("title") or ""),
                body=str(data.get("body") or ""),
                item_type=str(data.get("item_type") or SkillRuleItem.TYPE_RULE),
                payload=data.get("payload") if isinstance(data.get("payload"), dict) else {},
                priority=int(data.get("priority") or 100),
                sort_order=int(data.get("sort_order") or 0),
                version_tag=str(data.get("version_tag") or "v5.0.0"),
                status=str(data.get("status") or SkillRuleConfig.STATUS_DRAFT),
                note=str(data.get("note") or ""),
            )
        except (TypeError, ValueError) as exc:
            return api_fail(str(exc))
        return api_ok(SkillRuleItemService.serialize(row), message="规则条目已创建")


class SkillRuleItemDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, item_id=None):
        payload = SkillRuleItemService.get_item(item_id)
        if not payload:
            return api_fail("规则条目不存在", code=404)
        return api_ok(payload)

    def put(self, request, item_id=None):
        data = request.data or {}
        existing = SkillRuleItem.objects.filter(pk=item_id).first()
        if not existing:
            return api_fail("规则条目不存在", code=404)
        try:
            row = SkillRuleItemService.save_item(
                item_id=item_id,
                rule_key=str(data.get("rule_key") or existing.rule_key),
                tier=int(data.get("tier", existing.tier)),
                scope_type=str(data.get("scope_type") or existing.scope_type),
                scope_key=str(data.get("scope_key", existing.scope_key)),
                section=str(data.get("section") or existing.section),
                title=str(data.get("title") or existing.title),
                body=str(data.get("body") or existing.body),
                item_type=str(data.get("item_type") or existing.item_type),
                payload=data.get("payload") if isinstance(data.get("payload"), dict) else existing.payload,
                priority=int(data.get("priority", existing.priority)),
                sort_order=int(data.get("sort_order", existing.sort_order)),
                version_tag=str(data.get("version_tag") or existing.version_tag),
                status=str(data.get("status") or existing.status),
                note=str(data.get("note", existing.note)),
                config_id=str(existing.config_id) if existing.config_id else None,
            )
        except (TypeError, ValueError) as exc:
            return api_fail(str(exc))
        return api_ok(SkillRuleItemService.serialize(row), message="规则条目已更新")


class SkillRuleItemApproveView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, item_id=None):
        try:
            row = SkillRuleItemService.approve_item(
                item_id,
                approved_by=getattr(request.user, "username", "") or "admin",
            )
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(SkillRuleItemService.serialize(row), message="规则条目已批准生效")


class SkillRuleItemArchiveView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, item_id=None):
        try:
            SkillRuleItemService.archive_item(item_id)
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(None, message="规则条目已归档")


class SkillRuleItemFlattenView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        overwrite = (request.data or {}).get("overwrite", False) is True
        counts = SkillRuleItemService.flatten_from_configs(overwrite=overwrite)
        return api_ok(counts, message="规则条目拆分完成")
