"""创作者激励服务。"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from apps.operations.constants import PointsReason
from apps.operations.exceptions import CreatorError

from .models import (
    Badge,
    CreatorAchievement,
    CreatorLevel,
    CreatorProfile,
    PointsAccount,
    PointsTransaction,
)

logger = logging.getLogger(__name__)

# 默认积分规则（运营可在后台配置；此处为兜底）
DEFAULT_POINTS_RULES = {
    PointsReason.PROJECT_COMPLETED: 100,
    PointsReason.SCRIPT_ADOPTED: 50,
    PointsReason.TEMPLATE_USED: 5,
    PointsReason.TEMPLATE_RATED: 2,
    PointsReason.DAILY_LOGIN: 1,
    PointsReason.SHARE: 3,
    PointsReason.EXCHANGE: 0,  # 兑换由调用方指定 delta（负数）
    PointsReason.ADMIN_ADJUST: 0,  # 调整由调用方指定
}


# ──────────────────────────────────────────────
# 档案 / 等级
# ──────────────────────────────────────────────

@transaction.atomic
def get_or_create_profile(user) -> CreatorProfile:
    """懒加载创作者档案。"""
    profile, _ = CreatorProfile.objects.get_or_create(user=user)
    if not profile.level:
        # 默认绑到最低等级
        first = CreatorLevel.objects.filter(is_active=True).order_by("order", "min_points").first()
        if first:
            profile.level = first
            profile.save(update_fields=["level", "updated_at"])
    return profile


def evaluate_level(profile: CreatorProfile) -> CreatorProfile:
    """按 total_points 重新评估等级。"""
    target = (
        CreatorLevel.objects
        .filter(is_active=True, min_points__lte=profile.total_points)
        .order_by("-min_points")
        .first()
    )
    if target and target.pk != (profile.level_id or 0):
        profile.level = target
        profile.save(update_fields=["level", "updated_at"])
    return profile


# ──────────────────────────────────────────────
# 积分
# ──────────────────────────────────────────────

def get_points_account(user) -> PointsAccount:
    account, _ = PointsAccount.objects.get_or_create(user=user)
    return account


@transaction.atomic
def grant_points(
    *,
    user,
    delta: int,
    reason: str,
    ref_type: str = "",
    ref_id: str = "",
    note: str = "",
    operator: str = "",
) -> PointsTransaction:
    """发放 / 扣减积分（统一入口）。

    delta > 0 入账；delta < 0 消耗（要求余额充足）。
    """
    if not delta:
        raise CreatorError("delta 不能为 0")
    if reason not in PointsReason.values:
        raise CreatorError(f"未知 reason: {reason}")

    account = get_points_account(user)
    if delta < 0 and account.balance + delta < 0:
        raise CreatorError("积分余额不足")

    account.balance = F("balance") + delta
    if delta > 0:
        account.total_earned = F("total_earned") + delta
    else:
        account.total_spent = F("total_spent") + (-delta)
    account.last_change_at = timezone.now()
    account.save(update_fields=[
        "balance", "total_earned", "total_spent", "last_change_at", "updated_at",
    ])
    account.refresh_from_db(fields=["balance"])

    # 写流水
    tx = PointsTransaction.objects.create(
        user=user, delta=delta, reason=reason,
        ref_type=ref_type[:32], ref_id=ref_id[:64],
        note=note[:255], operator=operator[:64],
        balance_after=account.balance,
    )

    # 同步 profile
    profile = get_or_create_profile(user)
    CreatorProfile.objects.filter(pk=profile.pk).update(
        total_points=F("total_points") + (delta if delta > 0 else 0),
        available_points=F("available_points") + delta,
        used_points=F("used_points") + (-delta if delta < 0 else 0),
        updated_at=timezone.now(),
    )
    profile.refresh_from_db(fields=["total_points", "available_points", "used_points"])
    evaluate_level(profile)

    # 触发勋章检测
    _check_badges(user, reason=reason, ref_type=ref_type, ref_id=ref_id)

    logger.info(
        "creator.points grant user=%s delta=%s reason=%s balance=%s",
        user, delta, reason, account.balance,
    )
    return tx


@transaction.atomic
def admin_adjust(*, user, delta: int, operator: str, note: str = "") -> PointsTransaction:
    """运营人工调整。"""
    if not note:
        raise CreatorError("运营调整必须填写 note")
    return grant_points(
        user=user, delta=delta,
        reason=PointsReason.ADMIN_ADJUST,
        note=note, operator=operator,
    )


@transaction.atomic
def exchange(*, user, cost: int, note: str = "", ref_type: str = "reward", ref_id: str = "") -> PointsTransaction:
    """兑换消耗。"""
    if cost <= 0:
        raise CreatorError("兑换消耗必须 > 0")
    return grant_points(
        user=user, delta=-cost,
        reason=PointsReason.EXCHANGE,
        note=note or f"兑换 {ref_type}#{ref_id}",
        ref_type=ref_type, ref_id=ref_id,
    )


def auto_grant_for_event(*, user, reason: str, ref_type: str = "", ref_id: str = "") -> PointsTransaction | None:
    """事件驱动自动发分（用默认规则；idempotent：靠应用层去重）。"""
    amount = DEFAULT_POINTS_RULES.get(reason, 0)
    if not amount:
        return None
    return grant_points(
        user=user, delta=amount, reason=reason,
        ref_type=ref_type, ref_id=ref_id,
        note=f"auto:{reason}",
    )


# ──────────────────────────────────────────────
# 勋章
# ──────────────────────────────────────────────

@transaction.atomic
def _check_badges(user, *, reason: str, ref_type: str = "", ref_id: str = "") -> list[CreatorAchievement]:
    """根据事件检测勋章解锁。"""
    earned: list[CreatorAchievement] = []
    candidates = Badge.objects.filter(is_active=True).exclude(achievements__user=user)
    for badge in candidates:
        ok, progress = _badge_condition(badge, user, reason, ref_type, ref_id)
        if ok:
            ach = CreatorAchievement.objects.create(user=user, badge=badge, progress=100)
            earned.append(ach)
            logger.info("creator.badge.unlock user=%s badge=%s", user, badge.code)
    return earned


def _badge_condition(badge: Badge, user, reason: str, ref_type: str, ref_id: str) -> tuple[bool, int]:
    """根据 trigger_event + threshold 判定是否解锁。"""
    if not badge.trigger_event:
        return False, 0
    te = badge.trigger_event
    threshold = badge.trigger_threshold
    if te == "project_completed_count":
        n = PointsTransaction.objects.filter(
            user=user, reason=PointsReason.PROJECT_COMPLETED,
        ).count()
        return (n >= threshold, min(100, int(n * 100 / max(1, threshold))))
    if te == "template_use_count":
        n = PointsTransaction.objects.filter(
            user=user, reason=PointsReason.TEMPLATE_USED,
        ).count()
        return (n >= threshold, min(100, int(n * 100 / max(1, threshold))))
    if te == "total_points":
        profile = get_or_create_profile(user)
        return (profile.total_points >= threshold, min(100, int(profile.total_points * 100 / max(1, threshold))))
    if te == "first_event" and reason:
        return (True, 100)
    return False, 0


# ──────────────────────────────────────────────
# 运营：等级 / 勋章 CRUD
# ──────────────────────────────────────────────

@transaction.atomic
def upsert_level(
    *,
    code: str, name: str, min_points: int, max_points: int = 0,
    order: int = 0, benefits: list | None = None,
    is_active: bool = True, badge_icon: str = "",
) -> CreatorLevel:
    obj, _ = CreatorLevel.objects.update_or_create(
        code=code,
        defaults={
            "name": name, "min_points": min_points, "max_points": max_points,
            "order": order, "benefits": benefits or [],
            "is_active": is_active, "badge_icon": badge_icon,
        },
    )
    return obj


@transaction.atomic
def upsert_badge(
    *, code: str, name: str, description: str = "",
    trigger_event: str = "", trigger_threshold: int = 0,
    rarity: str = "common", icon_url: str = "",
    is_active: bool = True,
) -> Badge:
    obj, _ = Badge.objects.update_or_create(
        code=code,
        defaults={
            "name": name, "description": description,
            "trigger_event": trigger_event, "trigger_threshold": trigger_threshold,
            "rarity": rarity, "icon_url": icon_url, "is_active": is_active,
        },
    )
    return obj


@transaction.atomic
def grant_badge_manually(*, user, badge: Badge) -> CreatorAchievement:
    obj, created = CreatorAchievement.objects.get_or_create(user=user, badge=badge)
    return obj
