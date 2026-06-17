"""工单模型。"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.operations.constants import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)


class TicketCategoryConfig(models.Model):
    """工单分类配置（SLA + 默认处理人 + 模板）。

    支持运营在线维护：新建分类、调 SLA、调整默认处理组。
    """

    code = models.CharField(max_length=32, unique=True, choices=TicketCategory.choices)
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True, default="")
    sla_first_response_minutes = models.PositiveIntegerField(default=60)
    sla_resolve_minutes = models.PositiveIntegerField(default=1440)
    default_assignee_role = models.CharField(max_length=64, blank=True, default="")
    auto_reply_template = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_ticket_category"
        ordering = ["sort_order", "id"]


class Ticket(models.Model):
    """用户反馈工单。"""

    ticket_no = models.CharField(max_length=32, unique=True, help_text="工单编号（用户可见）")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name="tickets", null=True, blank=True,
    )
    category = models.CharField(max_length=32, choices=TicketCategory.choices)
    priority = models.CharField(
        max_length=8, choices=TicketPriority.choices, default=TicketPriority.P2,
    )
    status = models.CharField(
        max_length=16, choices=TicketStatus.choices, default=TicketStatus.PENDING,
    )
    subject = models.CharField(max_length=255)
    content = models.TextField()
    contact = models.CharField(max_length=128, blank=True, default="", help_text="联系方式（手机/邮箱/微信）")
    attachments = models.JSONField(default=list, help_text="附件 URL 列表")
    context = models.JSONField(default=dict, help_text="上下文：user_agent / 设备 / 关联项目 ID 等")
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name="assigned_tickets", null=True, blank=True,
    )
    assignee_role = models.CharField(max_length=64, blank=True, default="")
    first_response_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    sla_first_response_breached = models.BooleanField(default=False)
    sla_resolve_breached = models.BooleanField(default=False)
    satisfaction = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="用户满意度 1-5",
    )
    satisfaction_comment = models.TextField(blank=True, default="")
    operator = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_ticket"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["assignee", "status"]),
            models.Index(fields=["priority", "status"]),
            models.Index(fields=["-created_at"]),
        ]
        ordering = ["-created_at"]


class TicketReply(models.Model):
    """工单回复。"""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name="ticket_replies", null=True, blank=True,
    )
    author_role = models.CharField(max_length=16, help_text="user/ops/system", default="user")
    content = models.TextField()
    attachments = models.JSONField(default=list)
    is_internal_note = models.BooleanField(default=False, help_text="内部备注：用户不可见")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_ticket_reply"
        indexes = [models.Index(fields=["ticket", "-created_at"])]
        ordering = ["created_at"]


class TicketEvent(models.Model):
    """工单事件流水（状态变更 / 分派 / SLA 触发）。"""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=32, help_text="status_change / assign / sla_breach / reply")
    operator = models.CharField(max_length=64, blank=True, default="")
    from_value = models.CharField(max_length=64, blank=True, default="")
    to_value = models.CharField(max_length=64, blank=True, default="")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_ticket_event"
        indexes = [models.Index(fields=["ticket", "-created_at"])]
        ordering = ["-created_at"]


class TicketMacro(models.Model):
    """客服快捷回复模板。"""

    name = models.CharField(max_length=64)
    category = models.CharField(max_length=32, choices=TicketCategory.choices, blank=True, default="")
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    operator = models.CharField(max_length=64, blank=True, default="")
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_ticket_macro"
        ordering = ["-usage_count", "-created_at"]
