"""
订单模块 API 视图
"""
from rest_framework import status, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Order
from .serializers import (
    CreateOrderSerializer,
    OrderSerializer,
    OrderDetailSerializer,
    MockPaySerializer,
    PayResultSerializer,
)
from .services import OrderService, PaymentService


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
        return OrderService.get_order_detail(self.request.user, self.kwargs["pk"])

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
                {"success": False, "message": err},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "success": True,
                "message": "订单创建成功",
                "order": OrderDetailSerializer(order).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"])
    def mock_pay(self, request):
        """模拟支付回调：把订单改为已支付并开通会员"""
        serializer = MockPaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_no = serializer.validated_data["order_no"]

        ok, msg, order = PaymentService.process_mock_payment(order_no)
        if not ok:
            return Response(
                {"success": False, "message": msg, "order": None},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "success": True,
                "message": msg,
                "order": OrderDetailSerializer(order).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def cancel(self, request):
        """取消待支付订单"""
        order_no = request.data.get("order_no")
        if not order_no:
            return Response(
                {"success": False, "message": "请提供订单号"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ok, msg = OrderService.cancel_order(request.user, order_no)
        return Response(
            {"success": ok, "message": msg},
            status=status.HTTP_200_OK if ok else status.HTTP_400_BAD_REQUEST,
        )


class MyLatestOrderView(APIView):
    """我的最近一笔订单"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        order = (
            OrderService.get_user_orders(request.user).first()
        )
        if not order:
            return Response({"detail": "暂无订单"}, status=status.HTTP_200_OK)
        return Response(OrderDetailSerializer(order).data)
