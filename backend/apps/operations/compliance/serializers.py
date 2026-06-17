"""合规规则序列化器。"""
from __future__ import annotations

from rest_framework import serializers

from apps.operations.compliance.models import (
    ComplianceRule,
    ComplianceRuleVersion,
    SensitiveWord,
    TopicBlacklist,
    ViolationLog,
)


class SensitiveWordSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    level_display = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = SensitiveWord
        fields = [
            "id", "word", "category", "category_display",
            "level", "level_display", "description",
            "is_active", "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TopicBlacklistSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    level_display = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = TopicBlacklist
        fields = [
            "id", "name", "keywords", "category", "category_display",
            "level", "level_display", "reason", "is_active",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ComplianceRuleSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    level_display = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = ComplianceRule
        fields = [
            "id", "name", "description", "category", "category_display",
            "level", "level_display", "rule_expr", "scope",
            "is_active", "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ViolationLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default="")
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    level_display = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = ViolationLog
        fields = [
            "id", "user", "username", "project",
            "category", "category_display", "level", "level_display",
            "source", "matched_text", "rule_name", "action_taken",
            "handled", "handled_by", "handled_at", "handle_note", "created_at",
        ]
        read_only_fields = fields


class ComplianceRuleVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceRuleVersion
        fields = ["id", "version", "snapshot", "note", "published_by", "published_at"]
        read_only_fields = fields
