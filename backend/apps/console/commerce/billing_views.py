# -*- coding: utf-8 -*-
"""后台：币种设置 / 动作定价 / 流程编排"""
from decimal import Decimal

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import ActionPricing, AiFieldPromptConfig, RechargePackage, SiteCoinSettings
from apps.billing.commerce_pricing import discount_display_label, to_decimal
from apps.billing.services import BillingService
from apps.billing.ai_field_prompt_service import AiFieldPromptService
from apps.common.permissions import IsAdminUser

from apps.console.responses import api_fail, api_ok


def _apply_recharge_package_fields(row, data):
    if "name" in data:
        row.name = str(data["name"])[:64]
    if "price_yuan" in data:
        parsed = to_decimal(data["price_yuan"])
        if parsed is not None:
            row.price_yuan = parsed
    if "original_price_yuan" in data:
        raw = data["original_price_yuan"]
        row.original_price_yuan = to_decimal(raw) if raw not in (None, "") else None
    if "discount_percent" in data:
        parsed = to_decimal(data["discount_percent"])
        if parsed is not None:
            row.discount_percent = parsed
    if "base_coins" in data:
        row.base_coins = max(0, int(data["base_coins"]))
    if "bonus_coins" in data:
        row.bonus_coins = max(0, int(data["bonus_coins"]))
    if "is_active" in data:
        row.is_active = bool(data["is_active"])
    if "sort_order" in data:
        row.sort_order = int(data["sort_order"])
    return row


class SiteCoinSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        obj = SiteCoinSettings.load()
        return api_ok(
            {
                "currency_name": obj.currency_name,
                "signup_bonus": obj.signup_bonus,
                "default_pipeline_mode": obj.default_pipeline_mode,
                "require_membership_for_creation": obj.require_membership_for_creation,
                "updated_at": obj.updated_at,
            }
        )

    def put(self, request):
        obj = SiteCoinSettings.load()
        data = request.data or {}
        if "currency_name" in data:
            obj.currency_name = str(data["currency_name"])[:32] or obj.currency_name
        if "signup_bonus" in data:
            obj.signup_bonus = max(0, int(data["signup_bonus"]))
        if "default_pipeline_mode" in data and data["default_pipeline_mode"] in ("auto", "step"):
            obj.default_pipeline_mode = data["default_pipeline_mode"]
        if "require_membership_for_creation" in data:
            obj.require_membership_for_creation = bool(data["require_membership_for_creation"])
        obj.save()
        return api_ok({"currency_name": obj.currency_name}, message="站点币种设置已更新")


class ActionPricingListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        rows = ActionPricing.objects.all().order_by("sort_order", "action_key")
        items = [
            {
                "id": str(r.id),
                "action_key": r.action_key,
                "display_name": r.display_name,
                "coin_cost": r.coin_cost,
                "is_active": r.is_active,
                "sort_order": r.sort_order,
                "member_only": r.member_only,
            }
            for r in rows
        ]
        return api_ok(items)

    def post(self, request):
        data = request.data or {}
        key = (data.get("action_key") or "").strip()
        if not key:
            return api_fail("action_key 不能为空")
        row, _ = ActionPricing.objects.update_or_create(
            action_key=key,
            defaults={
                "display_name": data.get("display_name") or key,
                "coin_cost": max(0, int(data.get("coin_cost", 0))),
                "is_active": bool(data.get("is_active", True)),
                "sort_order": int(data.get("sort_order", 0)),
            },
        )
        return api_ok(
            {
                "id": str(row.id),
                "action_key": row.action_key,
                "display_name": row.display_name,
                "coin_cost": row.coin_cost,
            },
            message="定价已保存",
            http_status=status.HTTP_201_CREATED,
        )


class ActionPricingDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, pricing_id=None):
        try:
            row = ActionPricing.objects.get(pk=pricing_id)
        except ActionPricing.DoesNotExist:
            return api_fail("定价项不存在")
        data = request.data or {}
        if "display_name" in data:
            row.display_name = str(data["display_name"])[:100]
        if "coin_cost" in data:
            row.coin_cost = max(0, int(data["coin_cost"]))
        if "is_active" in data:
            row.is_active = bool(data["is_active"])
        if "sort_order" in data:
            row.sort_order = int(data["sort_order"])
        if "member_only" in data:
            row.member_only = bool(data["member_only"])
        row.save()
        return api_ok({"id": str(row.id), "coin_cost": row.coin_cost}, message="已更新")

    def delete(self, request, pricing_id=None):
        try:
            row = ActionPricing.objects.get(pk=pricing_id)
        except ActionPricing.DoesNotExist:
            return api_fail("定价项不存在")
        row.delete()
        return api_ok(None, message="已删除")


class RechargePackageListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        rows = RechargePackage.objects.all().order_by("sort_order", "price_yuan")
        items = [
            {
                "id": str(r.id),
                "name": r.name,
                "price_yuan": str(r.charge_price),
                "original_price_yuan": str(r.original_price_yuan) if r.original_price_yuan else None,
                "discount_percent": str(r.discount_percent),
                "discount_label": discount_display_label(r.discount_percent),
                "base_coins": r.base_coins,
                "bonus_coins": r.bonus_coins,
                "total_coins": r.total_coins,
                "is_active": r.is_active,
                "sort_order": r.sort_order,
            }
            for r in rows
        ]
        return api_ok(items)

    def post(self, request):
        data = request.data or {}
        name = (data.get("name") or "").strip()
        if not name:
            return api_fail("档位名称不能为空")
        row = RechargePackage.objects.create(
            name=name,
            price_yuan=to_decimal(data.get("price_yuan"), Decimal("0")) or Decimal("0"),
            original_price_yuan=to_decimal(data.get("original_price_yuan")),
            discount_percent=to_decimal(data.get("discount_percent"), Decimal("100")) or Decimal("100"),
            base_coins=max(0, int(data.get("base_coins", 0))),
            bonus_coins=max(0, int(data.get("bonus_coins", 0))),
            is_active=bool(data.get("is_active", True)),
            sort_order=int(data.get("sort_order", 0)),
        )
        return api_ok({"id": str(row.id)}, message="充值档位已创建", http_status=status.HTTP_201_CREATED)


class RechargePackageDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, package_id=None):
        try:
            row = RechargePackage.objects.get(pk=package_id)
        except RechargePackage.DoesNotExist:
            return api_fail("档位不存在")
        data = request.data or {}
        _apply_recharge_package_fields(row, data)
        row.save()
        return api_ok({"id": str(row.id)}, message="档位已更新")

    def delete(self, request, package_id=None):
        try:
            row = RechargePackage.objects.get(pk=package_id)
        except RechargePackage.DoesNotExist:
            return api_fail("档位不存在")
        row.delete()
        return api_ok(None, message="档位已删除")


class AiFieldPromptListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        return api_ok(AiFieldPromptService.list_admin_items())

    def post(self, request):
        data = request.data or {}
        key = (data.get("action_key") or "").strip()
        if not key:
            return api_fail("action_key 不能为空")
        row = AiFieldPromptService.upsert(key, data)
        return api_ok(
            {
                "id": str(row.id),
                "action_key": row.action_key,
                "display_name": row.display_name,
            },
            message="提示词已保存",
            http_status=status.HTTP_201_CREATED,
        )


class AiFieldPromptDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def put(self, request, prompt_id=None):
        try:
            row = AiFieldPromptConfig.objects.get(pk=prompt_id)
        except AiFieldPromptConfig.DoesNotExist:
            return api_fail("提示词配置不存在")
        data = request.data or {}
        if "display_name" in data:
            row.display_name = str(data["display_name"])[:100]
        if "system_prompt" in data:
            row.system_prompt = str(data["system_prompt"])
        if "user_prompt_tpl" in data:
            row.user_prompt_tpl = str(data["user_prompt_tpl"])
        if "system_prompt_fallback" in data:
            row.system_prompt_fallback = str(data["system_prompt_fallback"])
        if "response_json" in data:
            row.response_json = bool(data["response_json"])
        if "is_active" in data:
            row.is_active = bool(data["is_active"])
        if "sort_order" in data:
            row.sort_order = int(data["sort_order"])
        if "llm_provider_id" in data:
            from apps.skill.models import LlmProvider

            raw = data.get("llm_provider_id")
            if not raw:
                row.llm_provider = None
            else:
                row.llm_provider = LlmProvider.objects.filter(pk=raw, is_enabled=True).first()
        row.save()
        return api_ok({"id": str(row.id), "action_key": row.action_key}, message="提示词已更新")

    def delete(self, request, prompt_id=None):
        try:
            row = AiFieldPromptConfig.objects.get(pk=prompt_id)
        except AiFieldPromptConfig.DoesNotExist:
            return api_fail("提示词配置不存在")
        row.delete()
        return api_ok(None, message="已删除，运行时将回退代码默认值")


class AiFieldPromptSeedView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        created = AiFieldPromptService.seed_defaults()
        return api_ok({"created": created}, message="已从默认值写入数据库")
