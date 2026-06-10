"""
订单与支付业务逻辑 - 模拟支付回调
"""
import logging
from decimal import Decimal

from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from apps.membership.models import MembershipPlan
from apps.membership.services import MembershipService
from .models import Order, Payment

logger = logging.getLogger(__name__)


class OrderService:
    """订单业务服务"""

    @staticmethod
    @transaction.atomic
    def create_order(user, plan_id, payment_method="mock"):
        """创建会员购买订单

        返回 (订单对象, 错误信息) 元组
        """
        try:
            plan = MembershipPlan.objects.get(id=plan_id, is_active=True)
        except ObjectDoesNotExist:
            return None, "套餐不存在或已下架"

        order = Order(
            user=user,
            membership_plan=plan,
            amount=plan.price,
            status=Order.STATUS_PENDING,
            payment_method=payment_method,
        )
        order.save()
        logger.info("用户 %s 创建订单 %s，套餐 %s，金额 ¥%s", user, order.order_no, plan, plan.price)
        return order, None

    @staticmethod
    def get_user_orders(user, status=None):
        """获取用户订单列表"""
        qs = Order.objects.filter(user=user).select_related("membership_plan")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")

    @staticmethod
    def get_order_detail(user, order_id_or_no):
        """获取用户订单详情，校验归属"""
        try:
            order = (
                Order.objects.filter(user=user)
                .select_related("membership_plan")
                .prefetch_related("payments")
            )
            if isinstance(order_id_or_no, str) and len(order_id_or_no) > 16:
                order = order.filter(order_no=order_id_or_no)
            else:
                order = order.filter(id=order_id_or_no)
            return order.first()
        except Exception:
            return None

    @staticmethod
    @transaction.atomic
    def cancel_order(user, order_no):
        """用户取消待支付订单"""
        try:
            order = Order.objects.select_for_update().get(
                order_no=order_no, user=user, status=Order.STATUS_PENDING
            )
        except ObjectDoesNotExist:
            return False, "订单不存在或已支付"

        order.status = Order.STATUS_CANCELLED
        order.save()
        logger.info("用户 %s 取消订单 %s", user, order_no)
        return True, "取消成功"


class PaymentService:
    """支付业务服务（模拟支付网关）"""

    @staticmethod
    @transaction.atomic
    def create_mock_payment(order):
        """创建模拟支付记录"""
        payment = Payment(
            order=order,
            amount=order.amount,
            status=Payment.STATUS_PENDING,
        )
        payment.save()
        return payment

    @staticmethod
    @transaction.atomic
    def process_mock_payment(order_no):
        """模拟支付回调：把订单改为已支付，并开通会员

        返回 (成功与否, 消息, order)
        """
        try:
            order = Order.objects.select_for_update().get(order_no=order_no)
        except ObjectDoesNotExist:
            return False, "订单不存在", None

        if order.status == Order.STATUS_PAID:
            return True, "订单已支付", order
        if order.status != Order.STATUS_PENDING:
            return False, f"订单状态为 {order.get_status_display()}，无法支付", order

        payment = Payment(
            order=order,
            amount=order.amount,
            status=Payment.STATUS_SUCCESS,
            paid_at=timezone.now(),
            raw_response={
                "channel": "mock",
                "trade_status": "SUCCESS",
                "trade_no": f"MOCK{order.order_no}",
                "timestamp": timezone.now().isoformat(),
            },
        )
        payment.save()

        order.status = Order.STATUS_PAID
        order.paid_at = timezone.now()
        order.save()

        if order.membership_plan:
            MembershipService.activate_membership(
                order.user, order.membership_plan, order=order
            )

        logger.info(
            "订单 %s 模拟支付成功，用户 %s，金额 ¥%s",
            order.order_no,
            order.user,
            order.amount,
        )
        return True, "支付成功", order

    @staticmethod
    @transaction.atomic
    def refund_order(order_no, reason="手动退款"):
        """模拟退款

        仅将订单状态改为已退款；真实会员到期需要额外策略。
        """
        try:
            order = Order.objects.select_for_update().get(order_no=order_no)
        except ObjectDoesNotExist:
            return False, "订单不存在"

        if order.status != Order.STATUS_PAID:
            return False, "仅已支付订单可退款"

        order.status = Order.STATUS_REFUNDED
        order.save()

        Payment.objects.create(
            order=order,
            amount=-order.amount,
            status=Payment.STATUS_SUCCESS,
            paid_at=timezone.now(),
            raw_response={"action": "refund", "reason": reason},
        )
        logger.info("订单 %s 已退款：%s", order.order_no, reason)
        return True, "退款成功"
