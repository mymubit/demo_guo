"""创作者激励序列化器。"""
from __future__ import annotations

from rest_framework import serializers

from apps.operations.creator.models import (
    Badge,
    CreatorAchievement,
    CreatorLevel,
    CreatorProfile,
    PointsAccount,
    PointsTransaction,
)


class CreatorLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreatorLevel
        fields = [
            "id", "code", "name", "min_points", "max_points",
            "badge_icon", "benefits", "order", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = [
            "id", "code", "name", "description", "icon_url",
            "trigger_event", "trigger_threshold", "rarity",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CreatorAchievementSerializer(serializers.ModelSerializer):
    badge_name = serializers.CharField(source="badge.name", read_only=True, default="")
    badge_icon = serializers.CharField(source="badge.icon_url", read_only=True, default="")
    badge_rarity = serializers.CharField(source="badge.rarity", read_only=True, default="")

    class Meta:
        model = CreatorAchievement
        fields = ["id", "user", "badge", "badge_name", "badge_icon", "badge_rarity", "progress", "unlocked_at"]
        read_only_fields = ["id", "user", "progress", "unlocked_at"]


class CreatorProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default="")
    level_name = serializers.CharField(source="level.name", read_only=True, default="")
    level_code = serializers.CharField(source="level.code", read_only=True, default="")
    level_icon = serializers.CharField(source="level.badge_icon", read_only=True, default="")
    badge_list = CreatorAchievementSerializer(source="user.achievements", many=True, read_only=True)

    class Meta:
        model = CreatorProfile
        fields = [
            "id", "user", "username",
            "level", "level_code", "level_name", "level_icon",
            "total_points", "available_points", "used_points",
            "project_count", "template_count", "is_certified", "certified_at",
            "bio", "badge_list", "created_at", "updated_at",
        ]
        read_only_fields = fields


class PointsAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsAccount
        fields = [
            "id", "user", "balance", "total_earned", "total_spent",
            "frozen", "last_change_at", "created_at", "updated_at",
        ]
        read_only_fields = fields


class PointsTransactionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default="")
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = PointsTransaction
        fields = [
            "id", "user", "username", "delta", "reason", "reason_display",
            "ref_type", "ref_id", "note", "operator", "balance_after", "created_at",
        ]
        read_only_fields = fields
