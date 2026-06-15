"""
会员模块业务逻辑
"""
import logging
from decimal import Decimal
from datetime import timedelta

from django.utils import timezone
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist

from .models import MembershipPlan, UserMembership, PromoCode

logger = logging.getLogger(__name__)


class MembershipService:
    """会员业务服务"""

    @staticmethod
    def get_active_plan_list():
        """获取启用的套餐列表"""
        return MembershipPlan.objects.filter(is_active=True).order_by(
            "sort_order", "-created_at"
        )

    @staticmethod
    def get_current_membership(user):
        """获取用户当前有效的会员记录

        优先返回未过期且 is_active=True 的记录
        """
        now = timezone.now()
        return (
            UserMembership.objects.filter(
                user=user,
                is_active=True,
                end_at__gt=now,
            )
            .select_related("plan")
            .order_by("-end_at")
            .first()
        )

    @staticmethod
    def get_membership_summary(user):
        """获取会员状态摘要"""
        membership = MembershipService.get_current_membership(user)
        if not membership:
            wallet = {}
            try:
                from apps.billing.services import BillingService

                wallet = BillingService.get_wallet_summary(user)
            except Exception:  # noqa: BLE001
                pass
            return {
                "is_active": False,
                "plan_name": None,
                "remaining_days": 0,
                "remaining_creations": 0,
                "has_unlimited_creations": False,
                "end_at": None,
                "wallet": wallet,
            }
        remaining_days = max((membership.end_at - timezone.now()).days, 0)
        wallet = {}
        try:
            from apps.billing.services import BillingService

            wallet = BillingService.get_wallet_summary(user)
        except Exception:  # noqa: BLE001
            pass
        return {
            "is_active": membership.is_active and not membership.is_expired,
            "plan_name": membership.plan.name,
            "remaining_days": remaining_days,
            "remaining_creations": membership.remaining_creations,
            "has_unlimited_creations": membership.has_unlimited_creations,
            "end_at": membership.end_at,
            "wallet": wallet,
        }

    @staticmethod
    def create_membership_order(user, plan):
        """创建会员订单（供 orders 模块调用）

        返回 dict 以供订单生成使用。
        真实订单写入由 orders 模块完成。
        """
        if not plan.is_active:
            raise ValueError("该套餐已下架")
        return {
            "user": user,
            "plan": plan,
            "amount": plan.price,
            "validity_days": plan.validity_days,
            "creation_quota": plan.creation_quota,
        }

    @staticmethod
    @transaction.atomic
    def activate_membership(user, plan, order=None, grant_reference: str = ""):
        """激活/开通会员

        - 如果用户已有同类未过期会员：延长 end_at，叠加创作次数
        - 否则：新建一条 UserMembership
        """
        now = timezone.now()
        existing = (
            UserMembership.objects.filter(
                user=user,
                plan=plan,
                is_active=True,
                end_at__gt=now,
            )
            .select_for_update()
            .first()
        )

        if existing:
            grant_ref = (
                order.order_no
                if order
                else grant_reference or f"membership:{existing.id}:{now.isoformat()}"
            )
            existing.end_at = existing.end_at + timedelta(days=plan.validity_days)
            if plan.creation_quota > 0:
                existing.remaining_creations += plan.creation_quota
            existing.save()
            if plan.grant_coins > 0:
                from apps.billing.services import BillingService

                BillingService.credit(
                    user,
                    plan.grant_coins,
                    action_key="membership.grant",
                    reference_id=grant_ref,
                    remark=f"续费 {plan.name}",
                )
            if order:
                from apps.orders.models import MembershipGrant

                MembershipGrant.objects.get_or_create(
                    order=order,
                    defaults={
                        "user_membership": existing,
                        "grant_days": plan.validity_days,
                        "grant_coins": plan.grant_coins,
                    },
                )
            logger.info(
                "user=%s renew membership plan=%s end_at=%s",
                user.id,
                plan.id,
                existing.end_at,
            )
            return existing

        new_membership = UserMembership(
            user=user,
            plan=plan,
            start_at=now,
            end_at=now + timedelta(days=plan.validity_days),
            remaining_creations=plan.creation_quota,
            is_active=True,
        )
        new_membership.save()
        if plan.grant_coins > 0:
            from apps.billing.services import BillingService

            grant_ref = (
                order.order_no
                if order
                else grant_reference or f"membership:{new_membership.id}"
            )
            BillingService.credit(
                user,
                plan.grant_coins,
                action_key="membership.grant",
                reference_id=grant_ref,
                remark=f"开通 {plan.name}",
            )
        if order:
            from apps.orders.models import MembershipGrant

            MembershipGrant.objects.get_or_create(
                order=order,
                defaults={
                    "user_membership": new_membership,
                    "grant_days": plan.validity_days,
                    "grant_coins": plan.grant_coins,
                },
            )
        logger.info("user=%s activate membership plan=%s", user.id, plan.id)
        return new_membership

    @staticmethod
    @transaction.atomic
    def consume_creation(user):
        """扣除用户一次创作次数

        返回 (是否成功, 剩余次数或错误信息)
        """
        membership = MembershipService.get_current_membership(user)
        if not membership:
            return False, "无有效会员"
        if membership.has_unlimited_creations:
            return True, -1
        if membership.remaining_creations <= 0:
            return False, "创作次数不足"

        membership = (
            UserMembership.objects.select_for_update().get(pk=membership.pk)
        )
        membership.remaining_creations -= 1
        membership.save()
        return True, membership.remaining_creations

    @staticmethod
    def check_membership_status(user):
        """检查用户会员状态，返回 (是否有效, 信息)"""
        from apps.billing.services import BillingService

        settings_obj = BillingService.site_settings()
        if not settings_obj.require_membership_for_creation:
            return True, "开放创作"
        membership = MembershipService.get_current_membership(user)
        if not membership:
            return False, "无有效会员"
        return True, membership.plan.name

    @staticmethod
    @transaction.atomic
    def redeem_promo_code(user, code):
        """使用卡密兑换会员

        返回 (成功与否, 消息, user_membership, plan)
        """
        code = code.strip().upper()
        try:
            promo = PromoCode.objects.select_for_update().get(code=code)
        except ObjectDoesNotExist:
            return False, "卡密无效", None, None

        if not promo.is_active:
            return False, "卡密已被禁用", None, None
        if promo.is_expired:
            return False, "卡密已过期", None, None
        if promo.used_count >= promo.max_uses:
            return False, "卡密已被使用", None, None

        redemption_index = promo.used_count + 1
        updated = PromoCode.objects.filter(
            pk=promo.pk,
            is_active=True,
            used_count__lt=F("max_uses"),
        ).update(used_count=F("used_count") + 1)
        if not updated:
            return False, "卡密已被使用", None, None

        user_membership = MembershipService.activate_membership(
            user,
            promo.plan,
            grant_reference=f"promo:{promo.code}:{redemption_index}",
        )
        logger.info(
            "user=%s redeem promo=%s plan=%s",
            user.id,
            promo.code,
            promo.plan_id,
        )
        return True, "兑换成功", user_membership, promo.plan
