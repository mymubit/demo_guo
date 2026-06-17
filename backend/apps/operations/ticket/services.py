"""工单服务层。"""
from __future__ import annotations

import logging
import secrets
import string
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.operations.constants import TicketStatus
from apps.operations.exceptions import TicketNotFound, OperationsError

from .models import (
    Ticket,
    TicketCategoryConfig,
    TicketEvent,
    TicketMacro,
    TicketReply,
)

logger = logging.getLogger(__name__)

_TICKET_NO_ALPHABET = string.digits


def _gen_ticket_no() -> str:
    suffix = "".join(secrets.choice(_TICKET_NO_ALPHABET) for _ in range(8))
    return f"T{timezone.now().strftime('%Y%m%d')}{suffix}"


@transaction.atomic
def create_ticket(
    *,
    user=None,
    category: str,
    subject: str,
    content: str,
    contact: str = "",
    attachments: list | None = None,
    context: dict | None = None,
    priority: str = "P2",
) -> Ticket:
    """创建工单。"""
    cat = TicketCategoryConfig.objects.filter(code=category, is_active=True).first()
    sla_first = cat.sla_first_response_minutes if cat else 60
    sla_resolve = cat.sla_resolve_minutes if cat else 1440

    ticket = Ticket.objects.create(
        ticket_no=_gen_ticket_no(),
        user=user,
        category=category,
        priority=priority,
        status=TicketStatus.PENDING,
        subject=subject[:255],
        content=content,
        contact=contact[:128],
        attachments=attachments or [],
        context=context or {},
        assignee_role=cat.default_assignee_role if cat else "",
    )
    TicketEvent.objects.create(
        ticket=ticket, event_type="status_change",
        from_value="", to_value=TicketStatus.PENDING, note="工单创建",
    )
    return ticket


def transition_ticket(
    ticket: Ticket,
    *,
    to_status: str,
    operator: str = "",
    operator_user=None,
    note: str = "",
) -> Ticket:
    """工单状态机：pending → processing → waiting_user ↔ processing → resolved/closed/rejected。"""
    from_status = ticket.status
    valid = {
        TicketStatus.PENDING: {TicketStatus.PROCESSING, TicketStatus.REJECTED, TicketStatus.CLOSED},
        TicketStatus.PROCESSING: {TicketStatus.WAITING_USER, TicketStatus.RESOLVED, TicketStatus.CLOSED},
        TicketStatus.WAITING_USER: {TicketStatus.PROCESSING, TicketStatus.RESOLVED, TicketStatus.CLOSED},
        TicketStatus.RESOLVED: {TicketStatus.CLOSED, TicketStatus.PROCESSING},
        TicketStatus.CLOSED: set(),
        TicketStatus.REJECTED: set(),
    }
    if to_status not in valid.get(from_status, set()):
        raise OperationsError(f"非法状态转移：{from_status} → {to_status}")
    now = timezone.now()
    ticket.status = to_status
    if to_status == TicketStatus.RESOLVED and not ticket.resolved_at:
        ticket.resolved_at = now
    if to_status == TicketStatus.CLOSED and not ticket.closed_at:
        ticket.closed_at = now
    if to_status == TicketStatus.PROCESSING and not ticket.first_response_at:
        ticket.first_response_at = now
    ticket.operator = operator or ticket.operator
    ticket.save(update_fields=[
        "status", "first_response_at", "resolved_at", "closed_at",
        "operator", "updated_at",
    ])
    TicketEvent.objects.create(
        ticket=ticket, event_type="status_change",
        from_value=from_status, to_value=to_status,
        operator=operator, note=note,
    )
    return ticket


def assign_ticket(
    ticket: Ticket,
    *,
    assignee=None,
    assignee_role: str = "",
    operator: str = "",
) -> Ticket:
    from_value = ticket.assignee.username if ticket.assignee_id else ""
    ticket.assignee = assignee
    ticket.assignee_role = assignee_role
    ticket.operator = operator or ticket.operator
    ticket.save(update_fields=["assignee", "assignee_role", "operator", "updated_at"])
    TicketEvent.objects.create(
        ticket=ticket, event_type="assign",
        from_value=from_value,
        to_value=assignee.username if assignee else "",
        operator=operator,
    )
    return ticket


def add_reply(
    ticket: Ticket,
    *,
    content: str,
    author=None,
    author_role: str = "user",
    attachments: list | None = None,
    is_internal_note: bool = False,
    operator: str = "",
) -> TicketReply:
    reply = TicketReply.objects.create(
        ticket=ticket,
        author=author,
        author_role=author_role,
        content=content,
        attachments=attachments or [],
        is_internal_note=is_internal_note,
    )
    TicketEvent.objects.create(
        ticket=ticket, event_type="reply",
        operator=operator, note=f"{author_role} 回复",
    )
    # 用户回复 → 如已 resolved，自动转 processing 等待客服跟进
    if author_role == "user" and ticket.status == TicketStatus.RESOLVED:
        transition_ticket(
            ticket, to_status=TicketStatus.PROCESSING,
            operator=operator, note="用户追问，重开工单",
        )
    # 客服首次回复 → 记录 first_response_at
    if author_role == "ops" and not ticket.first_response_at:
        ticket.first_response_at = timezone.now()
        ticket.save(update_fields=["first_response_at", "updated_at"])
    return reply


def check_sla_breach() -> dict:
    """定时任务调用：扫描 SLA 违约工单。"""
    now = timezone.now()
    breached_first = 0
    breached_resolve = 0
    for cat in TicketCategoryConfig.objects.filter(is_active=True):
        if cat.sla_first_response_minutes:
            threshold = now - timedelta(minutes=cat.sla_first_response_minutes)
            qs = Ticket.objects.filter(
                category=cat.code,
                status__in=[TicketStatus.PENDING, TicketStatus.PROCESSING],
                first_response_at__isnull=True,
                created_at__lt=threshold,
                sla_first_response_breached=False,
            )
            for t in qs:
                t.sla_first_response_breached = True
                t.save(update_fields=["sla_first_response_breached", "updated_at"])
                TicketEvent.objects.create(
                    ticket=t, event_type="sla_breach", note=f"首响 SLA 违约：{cat.sla_first_response_minutes}min",
                )
                breached_first += 1
        if cat.sla_resolve_minutes:
            threshold = now - timedelta(minutes=cat.sla_resolve_minutes)
            qs = Ticket.objects.filter(
                category=cat.code,
                status__in=[TicketStatus.PENDING, TicketStatus.PROCESSING, TicketStatus.WAITING_USER],
                resolved_at__isnull=True,
                created_at__lt=threshold,
                sla_resolve_breached=False,
            )
            for t in qs:
                t.sla_resolve_breached = True
                t.save(update_fields=["sla_resolve_breached", "updated_at"])
                TicketEvent.objects.create(
                    ticket=t, event_type="sla_breach", note=f"解决 SLA 违约：{cat.sla_resolve_minutes}min",
                )
                breached_resolve += 1
    return {"breached_first": breached_first, "breached_resolve": breached_resolve}


def rate_satisfaction(
    ticket: Ticket,
    *,
    score: int,
    comment: str = "",
) -> Ticket:
    if not 1 <= score <= 5:
        raise OperationsError("满意度必须在 1-5 之间")
    ticket.satisfaction = score
    ticket.satisfaction_comment = comment[:500]
    ticket.save(update_fields=["satisfaction", "satisfaction_comment", "updated_at"])
    return ticket


def use_macro(macro: TicketMacro) -> TicketMacro:
    TicketMacro.objects.filter(id=macro.id).update(usage_count=macro.usage_count + 1)
    return macro
