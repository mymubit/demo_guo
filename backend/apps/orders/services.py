"""
订单与支付业务逻辑 - 模拟支付回调
"""
import logging
from decimal import Decimal

from django.utils import timezone
from django.conf import settings
from django.core.exceptions import PermissionDenied
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

        charge = plan.charge_price
        order = Order(
            user=user,
            membership_plan=plan,
            order_type=Order.TYPE_MEMBERSHIP,
            amount=charge,
            status=Order.STATUS_PENDING,
            payment_method=payment_method,
        )
        order.save()
        logger.info(
            "user=%s create membership order=%s plan=%s amount=%s",
            user.id,
            order.order_no,
            plan.id,
            charge,
        )
        return order, None

    @staticmethod
    @transaction.atomic
    def create_recharge_order(user, package_id, payment_method="mock"):
        """创建充值订单"""
        from apps.billing.models import RechargePackage
        from apps.billing.recharge_grant import resolve_recharge_grant_coins

        try:
            package = RechargePackage.objects.get(id=package_id, is_active=True)
        except ObjectDoesNotExist:
            return None, "充值档位不存在或已下架"

        charge = package.charge_price
        grant = resolve_recharge_grant_coins(package, user)
        order = Order(
            user=user,
            order_type=Order.TYPE_RECHARGE,
            recharge_package=package,
            amount=charge,
            coins_granted=grant["total_coins"],
            status=Order.STATUS_PENDING,
            payment_method=payment_method,
        )
        order.save()
        logger.info(
            "user=%s create recharge order=%s package=%s amount=%s coins=%s",
            user.id,
            order.order_no,
            package.id,
            charge,
            grant["total_coins"],
        )
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
        except (ObjectDoesNotExist, ValueError, TypeError):
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
    def process_mock_payment(order_no, *, user=None):
        """模拟支付回调：把订单改为已支付，并开通会员

        返回 (成功与否, 消息, order)
        """
        if not getattr(settings, "ALLOW_MOCK_PAYMENT", False) or not getattr(settings, "DEBUG", False):
            raise PermissionDenied("模拟支付已关闭")

        try:
            order = Order.objects.select_for_update().get(order_no=order_no)
        except ObjectDoesNotExist:
            return False, "订单不存在", None

        if user is not None and order.user_id != user.id:
            logger.warning(
                "用户 %s 尝试越权模拟支付订单 %s（订单用户 %s）",
                user.id,
                order_no,
                order.user_id,
            )
            return False, "无权操作该订单", None

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

        if order.order_type == Order.TYPE_RECHARGE:
            from apps.billing.services import BillingService

            coins = order.coins_granted or 0
            if coins > 0:
                BillingService.credit(
                    order.user,
                    coins,
                    action_key="recharge.grant",
                    reference_id=order.order_no,
                    remark=f"充值 {order.recharge_package.name if order.recharge_package else ''}",
                )
        elif order.membership_plan:
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
        """模拟退款，并同步冲正本订单发放的权益。"""
        try:
            order = Order.objects.select_for_update().get(order_no=order_no)
        except ObjectDoesNotExist:
            return False, "订单不存在"

        if order.status != Order.STATUS_PAID:
            return False, "仅已支付订单可退款"

        if order.order_type == Order.TYPE_RECHARGE and order.coins_granted > 0:
            from apps.billing.services import BillingService

            try:
                BillingService.reverse_credit(
                    order.user,
                    order.coins_granted,
                    action_key="recharge.refund",
                    reference_id=order.order_no,
                    remark=f"充值订单退款：{order.order_no}",
                )
            except Exception as exc:  # noqa: BLE001
                return False, f"创作币冲正失败：{exc}"

        if order.order_type == Order.TYPE_MEMBERSHIP and order.membership_plan:
            from datetime import timedelta

            from apps.billing.services import BillingService
            from apps.orders.models import MembershipGrant

            plan = order.membership_plan
            grant = (
                MembershipGrant.objects.select_related("user_membership")
                .filter(order=order)
                .first()
            )
            grant_coins = grant.grant_coins if grant else plan.grant_coins
            if grant_coins > 0:
                try:
                    BillingService.reverse_credit(
                        order.user,
                        grant_coins,
                        action_key="membership.refund",
                        reference_id=order.order_no,
                        remark=f"会员订单退款：{order.order_no}",
                    )
                except Exception as exc:  # noqa: BLE001
                    return False, f"会员赠币冲正失败：{exc}"
            if grant:
                membership = grant.user_membership
                membership = type(membership).objects.select_for_update().get(pk=membership.pk)
                membership.end_at = membership.end_at - timedelta(days=grant.grant_days)
                if plan.creation_quota > 0:
                    membership.remaining_creations = max(
                        0,
                        membership.remaining_creations - plan.creation_quota,
                    )
                if membership.end_at <= timezone.now():
                    membership.is_active = False
                membership.save(update_fields=["end_at", "remaining_creations", "is_active"])
            else:
                from apps.membership.models import UserMembership

                membership = (
                    UserMembership.objects.select_for_update()
                    .filter(user=order.user, plan=plan, is_active=True)
                    .order_by("-end_at")
                    .first()
                )
                if membership:
                    membership.end_at = membership.end_at - timedelta(days=plan.validity_days)
                    if plan.creation_quota > 0:
                        membership.remaining_creations = max(
                            0,
                            membership.remaining_creations - plan.creation_quota,
                        )
                    if membership.end_at <= timezone.now():
                        membership.is_active = False
                    membership.save(update_fields=["end_at", "remaining_creations", "is_active"])

        order.status = Order.STATUS_REFUNDED
        order.save(update_fields=["status"])

        Payment.objects.create(
            order=order,
            amount=-order.amount,
            status=Payment.STATUS_SUCCESS,
            paid_at=timezone.now(),
            raw_response={"action": "refund", "reason": reason},
        )
        logger.info("订单 %s 已退款：%s", order.order_no, reason)
        return True, "退款成功"
