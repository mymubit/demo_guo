"""
会员模块序列化器
"""
from rest_framework import serializers

from .models import MembershipPlan, UserMembership, PromoCode


class MembershipPlanSerializer(serializers.ModelSerializer):
    """会员套餐序列化器 - 列表/详情展示"""

    display_price = serializers.SerializerMethodField()
    validity_text = serializers.SerializerMethodField()
    creation_quota_text = serializers.SerializerMethodField()

    class Meta:
        model = MembershipPlan
        fields = [
            "id",
            "name",
            "price",
            "display_price",
            "validity_days",
            "validity_text",
            "creation_quota",
            "creation_quota_text",
            "features",
            "is_recommended",
        ]

    def get_display_price(self, obj) -> str:
        return f"¥{obj.price:.2f}"

    def get_validity_text(self, obj) -> str:
        return f"{obj.validity_days} 天"

    def get_creation_quota_text(self, obj) -> str:
        if obj.creation_quota == -1:
            return "无限"
        return f"{obj.creation_quota} 次"


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
