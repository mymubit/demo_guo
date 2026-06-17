# -*- coding: utf-8 -*-
"""operations 序列化器。"""
from __future__ import annotations

from rest_framework import serializers

from .models import CreationFeedback, OperationsDailyCache, UserBehaviorEvent


class UserBehaviorEventSerializer(serializers.ModelSerializer):
    """用户行为事件（前端上报 + 后端记录）。"""

    class Meta:
        model = UserBehaviorEvent
        fields = [
            "id", "event_name", "source", "user", "session_id",
            "project_id", "page", "payload", "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]


class UserBehaviorEventCreateSerializer(serializers.ModelSerializer):
    """前端上报入口（user 由 request 注入，不接受客户端值）。"""

    class Meta:
        model = UserBehaviorEvent
        fields = [
            "event_name", "session_id", "project_id", "page", "payload",
        ]


class CreationFeedbackSerializer(serializers.ModelSerializer):
    """用户反馈 序列化器（增/查）。"""

    user_nickname = serializers.SerializerMethodField()
    project_title = serializers.SerializerMethodField()
    handler_nickname = serializers.SerializerMethodField()
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CreationFeedback
        fields = [
            "id",
            "user",
            "user_nickname",
            "project",
            "project_title",
            "category",
            "category_display",
            "severity",
            "severity_display",
            "source",
            "source_display",
            "status",
            "status_display",
            "title",
            "content",
            "contact",
            "tags",
            "handler",
            "handler_nickname",
            "handled_at",
            "handler_note",
            "is_from_sample",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "user", "handler", "handled_at", "is_from_sample",
            "created_at", "updated_at",
        ]

    def get_user_nickname(self, obj):
        if not obj.user:
            return "匿名"
        return (
            getattr(obj.user, "nickname", "")
            or getattr(obj.user, "phone", "")
            or str(obj.user.pk)
        )

    def get_project_title(self, obj):
        if not obj.project:
            return ""
        return (obj.project.title or obj.project.theme or "未命名")[:200]

    def get_handler_nickname(self, obj):
        if not obj.handler:
            return ""
        return (
            getattr(obj.handler, "nickname", "")
            or getattr(obj.handler, "phone", "")
            or str(obj.handler.pk)
        )


class CreationFeedbackCreateSerializer(serializers.ModelSerializer):
    """用户主动提交反馈（不强制 user/project）。"""

    class Meta:
        model = CreationFeedback
        fields = [
            "project",
            "category",
            "severity",
            "title",
            "content",
            "contact",
            "tags",
        ]


class CreationFeedbackHandleSerializer(serializers.Serializer):
    """运营处理反馈：修改状态 / 添加备注 / 指派处理人。"""

    STATUS_CHOICES = [
        ("open", "待处理"),
        ("in_progress", "处理中"),
        ("resolved", "已处理"),
        ("wont_fix", "不处理"),
    ]
    status = serializers.ChoiceField(choices=STATUS_CHOICES, required=False)
    handler_note = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    handler = serializers.UUIDField(required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False)


class OperationsDailyCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationsDailyCache
        fields = [
            "id", "cache_date", "metric_type", "payload", "extra",
            "created_at", "updated_at",
        ]
