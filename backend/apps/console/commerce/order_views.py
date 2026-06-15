# -*- coding: utf-8 -*-
"""后台 API — 商业中心 — 订单"""
from django.core.cache import cache
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import IsAdminUser
from apps.common.pagination import StandardPagination
from apps.console.responses import (
    CACHE_KEY_DASHBOARD,
    api_fail,
    api_ok,
)

from apps.orders.models import Order
from apps.orders.services import PaymentService
from apps.console.serializers import AdminOrderSerializer, OrderRefundResultSerializer


# ============================================================
# 订单管理
# ============================================================

class OrderManagementViewSet(viewsets.GenericViewSet):
    """订单管理

    - list: GET /api/admin/orders/?status=&keyword=&page=&page_size=
    - refund: POST /api/admin/orders/<id>/refund/
    """

    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminOrderSerializer
    pagination_class = StandardPagination

    def _base_queryset(self):
        qs = (
            Order.objects.select_related("user", "membership_plan")
            .all()
            .order_by("-created_at")
        )
        status_filter = self.request.query_params.get("status")
        keyword = self.request.query_params.get("keyword", "").strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        if keyword:
            qs = qs.filter(
                Q(order_no__icontains=keyword)
                | Q(user__nickname__icontains=keyword)
                | Q(user__phone__icontains=keyword)
            )
        return qs

    def list(self, request, *args, **kwargs):
        qs = self._base_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return api_ok(serializer.data)

    @action(detail=True, methods=["post"], url_path="refund")
    def refund(self, request, pk=None):
        """退款：统一走支付服务，同步冲正会员/充值权益。"""
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return api_fail("订单不存在")

        ok, msg = PaymentService.refund_order(
            order.order_no,
            reason=request.data.get("reason", "后台手动退款"),
        )
        if not ok:
            return api_fail(msg)

        order.refresh_from_db()

        cache.delete(CACHE_KEY_DASHBOARD)
        data = {
            "order_id": order.pk,
            "order_no": order.order_no,
            "success": True,
            "message": "退款成功",
        }
        serializer = OrderRefundResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return api_ok(serializer.validated_data)
