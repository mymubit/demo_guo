"""
会员模块业务逻辑
"""
import logging
from decimal import Decimal
from datetime import timedelta

from django.utils import timezone
from django.db import transaction
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
            return {
                "is_active": False,
                "plan_name": None,
                "remaining_days": 0,
                "remaining_creations": 0,
                "has_unlimited_creations": False,
                "end_at": None,
            }
        remaining_days = max((membership.end_at - timezone.now()).days, 0)
        return {
            "is_active": membership.is_active and not membership.is_expired,
            "plan_name": membership.plan.name,
            "remaining_days": remaining_days,
            "remaining_creations": membership.remaining_creations,
            "has_unlimited_creations": membership.has_unlimited_creations,
            "end_at": membership.end_at,
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
    def activate_membership(user, plan, order=None):
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
            existing.end_at = existing.end_at + timedelta(days=plan.validity_days)
            if plan.creation_quota != -1:
                existing.remaining_creations += plan.creation_quota
            else:
                existing.remaining_creations = -1
            existing.save()
            logger.info("用户 %s 续费套餐 %s，新到期时间 %s", user, plan, existing.end_at)
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
        logger.info("用户 %s 开通新会员套餐 %s", user, plan)
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
        membership = MembershipService.get_current_membership(user)
        if not membership:
            return False, "无有效会员"
        if membership.has_unlimited_creations:
            return True, "无限创作次数"
        if membership.remaining_creations <= 0:
            return False, "创作次数已用完"
        return True, f"剩余 {membership.remaining_creations} 次"

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

        promo.used_count += 1
        promo.save()

        user_membership = MembershipService.activate_membership(user, promo.plan)
        logger.info("用户 %s 使用卡密 %s 兑换套餐 %s", user, code, promo.plan)
        return True, "兑换成功", user_membership, promo.plan
