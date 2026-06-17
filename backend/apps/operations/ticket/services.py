"""工单服务（精简版）。"""
from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from apps.operations.constants import TicketStatus
from apps.operations.exceptions import OpsError

from .models import Ticket, TicketReply

logger = logging.getLogger(__name__)


@transaction.atomic
def create_ticket(*, subject: str, content: str, user=None, contact: str = "",
                  priority: str = "P2") -> Ticket:
    return Ticket.objects.create(
        user=user,
        contact=contact[:128],
        subject=subject[:255],
        content=content,
        priority=priority,
    )


@transaction.atomic
def reply_ticket(*, ticket: Ticket, content: str, author=None, is_from_user: bool = True) -> TicketReply:
    """回复工单。"""
    r = TicketReply.objects.create(
        ticket=ticket, author=author, content=content, is_from_user=is_from_user,
    )
    if not is_from_user and ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.REPLIED
        ticket.save(update_fields=["status", "updated_at"])
    return r


@transaction.atomic
def close_ticket(ticket: Ticket) -> Ticket:
    ticket.status = TicketStatus.CLOSED
    ticket.closed_at = timezone.now()
    ticket.save(update_fields=["status", "closed_at", "updated_at"])
    return ticket


@transaction.atomic
def reopen_ticket(ticket: Ticket) -> Ticket:
    if ticket.status == TicketStatus.CLOSED:
        ticket.status = TicketStatus.OPEN
        ticket.closed_at = None
        ticket.save(update_fields=["status", "closed_at", "updated_at"])
    return ticket


@transaction.atomic
def set_priority(ticket: Ticket, *, priority: str) -> Ticket:
    ticket.priority = priority
    ticket.save(update_fields=["priority", "updated_at"])
    return ticket
