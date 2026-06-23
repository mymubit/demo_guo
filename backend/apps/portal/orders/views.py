# -*- coding: utf-8 -*-
"""
订单模块 API 视图
"""
from rest_framework import status, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from django.core.exceptions import PermissionDenied

from apps.orders.models import Order
from apps.orders.serializers import (
    CreateOrderSerializer,
    OrderSerializer,
    OrderDetailSerializer,
    MockPaySerializer,
    CancelOrderSerializer,
    PayResultSerializer,
)
from apps.orders.services import OrderService, PaymentService


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """订单列表 / 详情"""

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        status_filter = self.request.query_params.get("status")
        return OrderService.get_user_orders(self.request.user, status=status_filter)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderSerializer

    def get_object(self):
        order = OrderService.get_order_detail(self.request.user, self.kwargs["pk"])
        if order is None:
            raise NotFound("订单不存在")
        return order

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response({"code": 0, "message": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {"code": 0, "message": "success", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def create_order(self, request):
        """创建会员购买订单"""
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order, err = OrderService.create_order(
            request.user,
            serializer.validated_data["plan_id"],
            serializer.validated_data["payment_method"],
        )
        if err:
            return Response(
                {"code": 4001, "message": err, "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "code": 0,
                "message": "订单创建成功",
                "data": {"order": OrderDetailSerializer(order).data},
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"])
    def mock_pay(self, request):
        """模拟支付回调：把订单改为已支付并开通会员"""
        serializer = MockPaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_no = serializer.validated_data["order_no"]

        try:
            ok, msg, order = PaymentService.process_mock_payment(order_no, user=request.user)
        except PermissionDenied as exc:
            return Response(
                {"code": 403, "message": str(exc), "data": None},
                status=status.HTTP_200_OK,
            )
        if not ok:
            return Response(
                {"code": 4001, "message": msg, "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "code": 0,
                "message": msg,
                "data": {"order": OrderDetailSerializer(order).data},
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def cancel(self, request):
        """取消待支付订单"""
        serializer = CancelOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_no = serializer.validated_data["order_no"]
        ok, msg = OrderService.cancel_order(request.user, order_no)
        if ok:
            return Response(
                {"code": 0, "message": msg, "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 4001, "message": msg, "data": None},
            status=status.HTTP_200_OK,
        )


class MyLatestOrderView(APIView):
    """我的最近一笔订单"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        order = (
            OrderService.get_user_orders(request.user).first()
        )
        if not order:
            return Response(
                {"code": 0, "message": "success", "data": None},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 0, "message": "success", "data": OrderDetailSerializer(order).data},
            status=status.HTTP_200_OK,
        )
