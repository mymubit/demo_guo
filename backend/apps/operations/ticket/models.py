"""工单模型（精简版）。

只保留：Ticket + TicketReply
砍掉：TicketCategoryConfig（写死枚举）、TicketEvent（个人站没审计必要）、TicketMacro（自己有键盘就行）
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.operations.constants import TicketPriority, TicketStatus


class Ticket(models.Model):
    """用户反馈工单。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name="tickets", null=True, blank=True,
    )
    contact = models.CharField(max_length=128, blank=True, default="", help_text="联系方式")
    subject = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField(max_length=8, choices=TicketPriority.choices, default=TicketPriority.P2)
    status = models.CharField(max_length=16, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ops_ticket"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["priority", "status"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"#{self.pk} {self.subject[:30]}"


class TicketReply(models.Model):
    """工单回复。"""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="ticket_replies",
    )
    is_from_user = models.BooleanField(default=True, help_text="True=用户回复，False=运营回复")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_ticket_reply"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["ticket", "created_at"])]
