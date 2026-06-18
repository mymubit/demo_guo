"""
订单模块序列化器
"""
from decimal import Decimal
from rest_framework import serializers

from apps.membership.serializers import MembershipPlanSerializer
from .models import Order, Payment


class CreateOrderSerializer(serializers.Serializer):
    """创建订单输入"""

    plan_id = serializers.UUIDField(help_text="会员套餐 ID")
    payment_method = serializers.ChoiceField(
        choices=["mock"],
        default="mock",
    )


class OrderSerializer(serializers.ModelSerializer):
    """订单序列化器"""

    status_text = serializers.CharField(source="get_status_display", read_only=True)
    payment_method_text = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    membership_plan = MembershipPlanSerializer(read_only=True)
    display_amount = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_no",
            "order_type",
            "plan_name",
            "amount",
            "display_amount",
            "status",
            "status_text",
            "payment_method",
            "payment_method_text",
            "membership_plan",
            "coins_granted",
            "paid_at",
            "created_at",
        ]

    def get_plan_name(self, obj) -> str:
        if obj.membership_plan:
            return obj.membership_plan.name
        if obj.recharge_package:
            return obj.recharge_package.name
        return ""

    def get_display_amount(self, obj) -> str:
        return f"¥{obj.amount:.2f}"


class PaymentSerializer(serializers.ModelSerializer):
    """支付记录序列化器"""

    status_text = serializers.CharField(source="get_status_display", read_only=True)
    display_amount = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "transaction_id",
            "amount",
            "display_amount",
            "status",
            "status_text",
            "paid_at",
            "created_at",
        ]

    def get_display_amount(self, obj) -> str:
        return f"¥{obj.amount:.2f}"


class OrderDetailSerializer(serializers.ModelSerializer):
    """订单详情（含支付记录）"""

    status_text = serializers.CharField(source="get_status_display", read_only=True)
    payment_method_text = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    membership_plan = MembershipPlanSerializer(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    display_amount = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_no",
            "order_type",
            "plan_name",
            "amount",
            "display_amount",
            "status",
            "status_text",
            "payment_method",
            "payment_method_text",
            "membership_plan",
            "coins_granted",
            "paid_at",
            "created_at",
            "payments",
        ]

    def get_plan_name(self, obj) -> str:
        if obj.membership_plan:
            return obj.membership_plan.name
        if obj.recharge_package:
            return obj.recharge_package.name
        return ""

    def get_display_amount(self, obj) -> str:
        return f"¥{obj.amount:.2f}"


class MockPaySerializer(serializers.Serializer):
    """模拟支付输入"""

    order_no = serializers.CharField(max_length=64)


class CancelOrderSerializer(serializers.Serializer):
    """取消订单输入"""

    order_no = serializers.RegexField(
        regex=r"^SF[0-9A-F]{14,32}$",
        max_length=64,
        error_messages={"invalid": "订单号格式不正确"},
    )


class PayResultSerializer(serializers.Serializer):
    """支付返回"""

    success = serializers.BooleanField()
    message = serializers.CharField()
    order = OrderDetailSerializer(allow_null=True)
