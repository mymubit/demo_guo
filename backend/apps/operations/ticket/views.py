"""工单 API。"""
from __future__ import annotations

import logging

from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok
from apps.operations.exceptions import OperationsError
from apps.operations.permissions import DOMAIN_SUPPORT, HasOpsDomain
from apps.operations.ticket import services
from apps.operations.ticket.models import (
    Ticket,
    TicketCategoryConfig,
    TicketEvent,
    TicketMacro,
    TicketReply,
)
from apps.operations.ticket.serializers import (
    TicketCategoryConfigSerializer,
    TicketEventSerializer,
    TicketMacroSerializer,
    TicketReplySerializer,
    TicketSerializer,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 客服 / 运营后台
# ──────────────────────────────────────────────
class TicketViewSet(ModelViewSet):
    """工单管理（运营 + 客服）。"""

    queryset = Ticket.objects.all().select_related("user", "assignee")
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_SUPPORT
    search_fields = ["ticket_no", "subject", "content", "user__username", "contact"]
    filterset_fields = ["status", "category", "priority", "assignee"]

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        ticket = self.get_object()
        data = request.data or {}
        try:
            ticket = services.transition_ticket(
                ticket,
                to_status=data.get("status", ""),
                operator=getattr(request.user, "username", ""),
                note=str(data.get("note", ""))[:500],
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(TicketSerializer(ticket).data, message="状态已变更")

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        ticket = self.get_object()
        assignee_id = request.data.get("assignee_id")
        assignee = None
        if assignee_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            assignee = User.objects.filter(id=assignee_id).first()
        ticket = services.assign_ticket(
            ticket,
            assignee=assignee,
            assignee_role=str(request.data.get("assignee_role", ""))[:64],
            operator=getattr(request.user, "username", ""),
        )
        return api_ok(TicketSerializer(ticket).data, message="分派成功")

    @action(detail=True, methods=["post"], url_path="reply")
    def reply(self, request, pk=None):
        ticket = self.get_object()
        content = str(request.data.get("content", "")).strip()
        if not content:
            return api_fail("回复内容不能为空", code=400)
        reply = services.add_reply(
            ticket,
            content=content,
            author=request.user,
            author_role="ops",
            attachments=request.data.get("attachments") or [],
            is_internal_note=bool(request.data.get("is_internal_note")),
            operator=getattr(request.user, "username", ""),
        )
        return api_ok(TicketReplySerializer(reply).data, message="已回复")

    @action(detail=True, methods=["post"], url_path="rate")
    def rate(self, request, pk=None):
        ticket = self.get_object()
        try:
            score = int(request.data.get("score", 0))
        except (TypeError, ValueError):
            return api_fail("score 必填且为整数", code=400)
        try:
            ticket = services.rate_satisfaction(
                ticket, score=score, comment=str(request.data.get("comment", "")),
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(TicketSerializer(ticket).data, message="已评分")

    @action(detail=False, methods=["get"], url_path="overview")
    def overview(self, request):
        qs = Ticket.objects.all()
        by_status = list(qs.values("status").annotate(count=Count("id")))
        by_priority = list(qs.values("priority").annotate(count=Count("id")))
        by_category = list(qs.values("category").annotate(count=Count("id")))
        sla_breached = qs.filter(
            Q(sla_first_response_breached=True) | Q(sla_resolve_breached=True),
        ).count()
        return api_ok({
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            "sla_breached_count": sla_breached,
        })


class TicketCategoryConfigViewSet(ModelViewSet):
    """工单分类配置（SLA 维护）。"""

    queryset = TicketCategoryConfig.objects.all()
    serializer_class = TicketCategoryConfigSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_SUPPORT
    search_fields = ["name", "code"]
    filterset_fields = ["is_active"]


class TicketMacroViewSet(ModelViewSet):
    """客服快捷回复模板。"""

    queryset = TicketMacro.objects.all()
    serializer_class = TicketMacroSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_SUPPORT
    search_fields = ["name", "content"]
    filterset_fields = ["category", "is_active"]


class TicketEventViewSet(ReadOnlyModelViewSet):
    """工单事件流水查询。"""

    queryset = TicketEvent.objects.all().order_by("-created_at")
    serializer_class = TicketEventSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, HasOpsDomain]
    ops_domain = DOMAIN_SUPPORT
    filterset_fields = ["ticket", "event_type"]


# ──────────────────────────────────────────────
# C 端用户接口
# ──────────────────────────────────────────────
class UserTicketCreateView(GenericAPIView):
    """C 端：用户提交工单。"""

    permission_classes = [IsAuthenticated]
    serializer_class = TicketSerializer

    def post(self, request):
        data = request.data or {}
        subject = str(data.get("subject", "")).strip()
        content = str(data.get("content", "")).strip()
        if not subject or not content:
            return api_fail("主题与内容必填", code=400)
        try:
            ticket = services.create_ticket(
                user=request.user,
                category=str(data.get("category", "other")),
                subject=subject,
                content=content,
                contact=str(data.get("contact", ""))[:128],
                attachments=data.get("attachments") or [],
                context=data.get("context") or {},
                priority=str(data.get("priority", "P2")),
            )
        except OperationsError as e:
            return api_fail(e.message, code=e.code)
        return api_ok(TicketSerializer(ticket).data, message="工单已创建")


class UserTicketListView(GenericAPIView):
    """C 端：我的工单列表。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Ticket.objects.filter(user=request.user).order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return api_ok(TicketSerializer(qs[:50], many=True).data)


class UserTicketReplyView(GenericAPIView):
    """C 端：用户回复/追问。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, ticket_id: int):
        try:
            ticket = Ticket.objects.get(id=ticket_id, user=request.user)
        except Ticket.DoesNotExist:
            return api_fail("工单不存在", code=404, http_status=status.HTTP_404_NOT_FOUND)
        content = str(request.data.get("content", "")).strip()
        if not content:
            return api_fail("回复内容不能为空", code=400)
        reply = services.add_reply(
            ticket,
            content=content,
            author=request.user,
            author_role="user",
            attachments=request.data.get("attachments") or [],
        )
        return api_ok(TicketReplySerializer(reply).data, message="已提交")
