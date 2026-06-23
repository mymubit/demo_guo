# -*- coding: utf-8 -*-
"""
会员模块序列化器
"""
from decimal import Decimal

from rest_framework import serializers

from apps.billing.commerce_pricing import discount_display_label
from .models import MembershipPlan, UserMembership, PromoCode


class MembershipPlanSerializer(serializers.ModelSerializer):
    """会员套餐序列化器 - 列表/详情展示"""

    display_price = serializers.SerializerMethodField()
    display_original_price = serializers.SerializerMethodField()
    discount_label = serializers.SerializerMethodField()
    validity_text = serializers.SerializerMethodField()
    grant_coins_text = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    class Meta:
        model = MembershipPlan
        fields = [
            "id",
            "name",
            "price",
            "original_price",
            "discount_percent",
            "display_price",
            "display_original_price",
            "discount_label",
            "validity_days",
            "validity_text",
            "grant_coins",
            "grant_coins_text",
            "features",
            "is_recommended",
        ]

    def get_display_price(self, obj) -> str:
        return f"¥{obj.charge_price:.2f}"

    def get_display_original_price(self, obj) -> str | None:
        charge = obj.charge_price
        if obj.original_price and obj.original_price > charge:
            return f"¥{obj.original_price:.2f}"
        from apps.billing.commerce_pricing import normalize_discount_percent, quantize_yuan

        discount = normalize_discount_percent(obj.discount_percent)
        if discount < Decimal("100") and charge > 0:
            derived = quantize_yuan(charge * Decimal("100") / discount)
            if derived > charge:
                return f"¥{derived:.2f}"
        return None

    def get_discount_label(self, obj) -> str | None:
        return discount_display_label(obj.discount_percent)

    def get_validity_text(self, obj) -> str:
        return f"{obj.validity_days} 天"

    def get_grant_coins_text(self, obj) -> str:
        return f"{obj.grant_coins} 创作币" if obj.grant_coins else ""

    def get_features(self, obj) -> list:
        """C 端套餐卡片：开通赠币 + 全局会员权益（各档位功能相同）。"""
        from .feature_matrix_service import FeatureMatrixService

        items = []
        if obj.grant_coins:
            items.append(f"开通赠送 {obj.grant_coins} 创作币")
        for row in FeatureMatrixService.resolve_matrix():
            if row.get("member"):
                label = str(row.get("label") or "").strip()
                if label and label not in items:
                    items.append(label)
        return items


class UserMembershipSerializer(serializers.ModelSerializer):
    """我的会员信息序列化器"""

    plan = MembershipPlanSerializer(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    has_unlimited_creations = serializers.BooleanField(read_only=True)
    remaining_days = serializers.SerializerMethodField()

    class Meta:
        model = UserMembership
        fields = [
            "id",
            "plan",
            "start_at",
            "end_at",
            "remaining_days",
            "remaining_creations",
            "has_unlimited_creations",
            "is_active",
            "is_expired",
            "created_at",
        ]

    def get_remaining_days(self, obj) -> int:
        from django.utils import timezone

        if obj.end_at < timezone.now():
            return 0
        return (obj.end_at - timezone.now()).days


class UserMembershipSummarySerializer(serializers.Serializer):
    """会员状态摘要"""

    is_active = serializers.BooleanField()
    plan_name = serializers.CharField(allow_null=True)
    remaining_days = serializers.IntegerField()
    remaining_creations = serializers.IntegerField()
    has_unlimited_creations = serializers.BooleanField()
    end_at = serializers.DateTimeField(allow_null=True)
    wallet = serializers.DictField(required=False, allow_null=True)


class RedeemPromoCodeSerializer(serializers.Serializer):
    """卡密兑换输入"""

    code = serializers.CharField(
        max_length=50,
        error_messages={"blank": "请输入卡密", "max_length": "卡密长度不正确"},
    )

    def validate_code(self, value):
        code = value.strip().upper()
        if not code:
            raise serializers.ValidationError("请输入卡密")
        return code


class RedeemPromoCodeResultSerializer(serializers.Serializer):
    """卡密兑换返回"""

    success = serializers.BooleanField()
    message = serializers.CharField()
    plan = MembershipPlanSerializer(allow_null=True)
    user_membership = UserMembershipSerializer(allow_null=True)
