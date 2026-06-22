# -*- coding: utf-8 -*-
"""后台：技能规则库 SkillRuleConfig。"""
from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.skill.models import SkillRuleConfig
from apps.skill.skills.admin_service import SkillRuleConfigService
from apps.skill.skills.rule_item_service import SkillRuleItemService

from apps.console.responses import api_fail, api_ok


class SkillRuleListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        tier = request.query_params.get("tier")
        status = request.query_params.get("status")
        scope_type = request.query_params.get("scope_type")
        q = request.query_params.get("q") or ""
        try:
            tier_val = int(tier) if tier not in (None, "") else None
        except ValueError:
            return api_fail("tier 参数无效")
        SkillRuleConfigService.ensure_defaults()
        exclude_bundle = request.query_params.get("exclude_bundle", "true").strip().lower() not in (
            "0",
            "false",
            "no",
        )
        items = SkillRuleConfigService.list_rules(
            tier=tier_val,
            status=status or None,
            scope_type=scope_type or None,
            q=q,
            exclude_bundle=exclude_bundle,
        )
        return api_ok({"items": items, "summary": SkillRuleConfigService.summary()})

    def post(self, request):
        data = request.data or {}
        try:
            row = SkillRuleConfigService.save_rule(
                tier=int(data.get("tier")),
                scope_type=str(data.get("scope_type") or SkillRuleConfig.SCOPE_GLOBAL),
                scope_key=str(data.get("scope_key") or ""),
                section=str(data.get("section") or "custom"),
                content=data.get("content") or {},
                version_tag=str(data.get("version_tag") or "v5.0.0"),
                status=str(data.get("status") or SkillRuleConfig.STATUS_DRAFT),
                note=str(data.get("note") or ""),
            )
        except (TypeError, ValueError) as exc:
            return api_fail(str(exc))
        return api_ok(SkillRuleConfigService.serialize(row), message="规则已保存")


class SkillRuleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, rule_id=None):
        payload = SkillRuleConfigService.get_rule(rule_id)
        if not payload:
            return api_fail("规则不存在", code=404)
        return api_ok(payload)

    def put(self, request, rule_id=None):
        data = request.data or {}
        try:
            row = SkillRuleConfigService.save_rule(
                rule_id=rule_id,
                tier=int(data.get("tier")),
                scope_type=str(data.get("scope_type") or SkillRuleConfig.SCOPE_GLOBAL),
                scope_key=str(data.get("scope_key") or ""),
                section=str(data.get("section") or "custom"),
                content=data.get("content") or {},
                version_tag=str(data.get("version_tag") or "v5.0.0"),
                status=str(data.get("status") or SkillRuleConfig.STATUS_DRAFT),
                note=str(data.get("note") or ""),
                approved_by=getattr(request.user, "username", "") or "admin",
            )
        except (TypeError, ValueError) as exc:
            return api_fail(str(exc))
        return api_ok(SkillRuleConfigService.serialize(row), message="规则已更新")


class SkillRuleApproveView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, rule_id=None):
        try:
            row = SkillRuleConfigService.approve_rule(
                rule_id,
                approved_by=getattr(request.user, "username", "") or "admin",
            )
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(SkillRuleConfigService.serialize(row), message="规则已批准生效")


class SkillRuleArchiveView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, rule_id=None):
        try:
            SkillRuleConfigService.archive_rule(rule_id)
        except ValueError as exc:
            return api_fail(str(exc))
        return api_ok(None, message="规则已归档")


class SkillRuleImportView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        overwrite = (request.data or {}).get("overwrite", True) is not False
        counts = SkillRuleConfigService.import_from_files(overwrite=overwrite)
        flat = SkillRuleItemService.flatten_from_configs(overwrite=overwrite)
        return api_ok({"counts": counts, "flatten": flat}, message="已从 skill-rules 目录导入并拆分条目")
