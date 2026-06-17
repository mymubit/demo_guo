"""工单序列化器。"""
from __future__ import annotations

from rest_framework import serializers

from apps.operations.ticket.models import (
    Ticket,
    TicketCategoryConfig,
    TicketEvent,
    TicketMacro,
    TicketReply,
)


class TicketCategoryConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCategoryConfig
        fields = [
            "id", "code", "name", "description",
            "sla_first_response_minutes", "sla_resolve_minutes",
            "default_assignee_role", "auto_reply_template",
            "is_active", "sort_order", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TicketReplySerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True, default="")

    class Meta:
        model = TicketReply
        fields = [
            "id", "ticket", "author", "author_name", "author_role",
            "content", "attachments", "is_internal_note", "created_at",
        ]
        read_only_fields = ["author", "created_at"]


class TicketEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketEvent
        fields = [
            "id", "ticket", "event_type", "operator",
            "from_value", "to_value", "note", "created_at",
        ]
        read_only_fields = fields


class TicketSerializer(serializers.ModelSerializer):
    replies = TicketReplySerializer(many=True, read_only=True)
    events = TicketEventSerializer(many=True, read_only=True)
    username = serializers.CharField(source="user.username", read_only=True, default="")
    assignee_name = serializers.CharField(source="assignee.username", read_only=True, default="")
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id", "ticket_no", "user", "username",
            "category", "category_name", "priority", "status",
            "subject", "content", "contact", "attachments", "context",
            "assignee", "assignee_name", "assignee_role",
            "first_response_at", "resolved_at", "closed_at",
            "sla_first_response_breached", "sla_resolve_breached",
            "satisfaction", "satisfaction_comment", "operator",
            "replies", "events", "created_at", "updated_at",
        ]
        read_only_fields = [
            "ticket_no", "first_response_at", "resolved_at", "closed_at",
            "sla_first_response_breached", "sla_resolve_breached",
            "operator", "replies", "events", "created_at", "updated_at",
        ]

    def get_category_name(self, obj: Ticket) -> str:
        cfg = TicketCategoryConfig.objects.filter(code=obj.category).first()
        return cfg.name if cfg else obj.get_category_display()


class TicketMacroSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMacro
        fields = [
            "id", "name", "category", "content",
            "is_active", "operator", "usage_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["usage_count", "created_at", "updated_at"]
