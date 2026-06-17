"""运营活动序列化器。"""
from __future__ import annotations

from rest_framework import serializers

from apps.operations.campaign.models import (
    Campaign,
    CouponClaimLog,
    CouponTemplate,
    RedemptionCode,
    RedemptionCodeBatch,
    UserCoupon,
)


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            "id", "slug", "name", "campaign_type", "status",
            "start_at", "end_at", "description", "rules",
            "target_user_filter", "max_claim_per_user", "total_quota",
            "claimed_count", "created_by", "operator",
            "created_at", "updated_at",
        ]
        read_only_fields = ["claimed_count", "created_at", "updated_at"]


class CouponTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponTemplate
        fields = [
            "id", "campaign", "name", "coupon_type", "value",
            "min_spend", "valid_days", "total_quota", "issued_count",
            "status", "scope", "extra", "created_at", "updated_at",
        ]
        read_only_fields = ["issued_count", "created_at", "updated_at"]


class UserCouponSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    campaign_name = serializers.CharField(source="campaign.name", read_only=True, default="")
    coupon_type = serializers.CharField(source="template.coupon_type", read_only=True)

    class Meta:
        model = UserCoupon
        fields = [
            "id", "code", "template", "template_name", "campaign",
            "campaign_name", "coupon_type", "status",
            "value_snapshot", "min_spend_snapshot",
            "valid_from", "valid_to", "used_at", "claim_source",
            "created_at",
        ]
        read_only_fields = fields


class RedemptionCodeBatchSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    campaign_name = serializers.CharField(source="campaign.name", read_only=True, default="")

    class Meta:
        model = RedemptionCodeBatch
        fields = [
            "id", "campaign", "campaign_name", "template", "template_name",
            "name", "code_length", "total_count", "issued_count", "claimed_count",
            "prefix", "note", "operator", "created_at",
        ]
        read_only_fields = ["issued_count", "claimed_count", "created_at"]


class RedemptionCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RedemptionCode
        fields = [
            "id", "batch", "code", "status", "user", "user_coupon",
            "claimed_at", "expires_at", "created_at",
        ]
        read_only_fields = ["user", "user_coupon", "claimed_at", "created_at"]


class CouponClaimLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default="")
    campaign_name = serializers.CharField(source="campaign.name", read_only=True, default="")

    class Meta:
        model = CouponClaimLog
        fields = [
            "id", "user", "username", "campaign", "campaign_name",
            "template", "user_coupon", "claim_source", "result",
            "reason", "ip", "user_agent", "created_at",
        ]
        read_only_fields = fields
