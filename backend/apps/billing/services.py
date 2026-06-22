# -*- coding: utf-8 -*-
"""币种扣费、钱包、流程编排读取。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import F

from apps.common.agent_term import alias_agent_id

from .models import ActionPricing, CoinLedger, SiteCoinSettings, UserWallet

logger = logging.getLogger(__name__)


class InsufficientCoins(PermissionDenied):
    """余额不足"""


class BillingService:
    @staticmethod
    def site_settings() -> SiteCoinSettings:
        return SiteCoinSettings.load()

    @staticmethod
    def currency_name() -> str:
        return BillingService.site_settings().currency_name

    @staticmethod
    @transaction.atomic
    def get_or_create_wallet(user) -> UserWallet:
        wallet, created = UserWallet.objects.select_for_update().get_or_create(
            user=user,
            defaults={"balance": 0},
        )
        if created:
            bonus = BillingService.site_settings().signup_bonus
            if bonus > 0:
                BillingService._apply_delta(
                    wallet,
                    bonus,
                    entry_type=CoinLedger.TYPE_GRANT,
                    action_key="signup.bonus",
                    remark="注册赠送",
                )
        return wallet

    @staticmethod
    def get_balance(user) -> int:
        wallet = UserWallet.objects.filter(user=user).first()
        return wallet.balance if wallet else 0

    @staticmethod
    def get_wallet_summary(user) -> Dict[str, Any]:
        settings_obj = BillingService.site_settings()
        wallet = BillingService.get_or_create_wallet(user)
        balance = wallet.balance
        auto_cost = BillingService.estimate_auto_pipeline_cost()
        estimated = balance // auto_cost if auto_cost > 0 else 0
        return {
            "currency_name": settings_obj.currency_name,
            "balance": balance,
            "signup_bonus": settings_obj.signup_bonus,
            "estimated_auto_cost": auto_cost,
            "estimated_scripts_remaining": estimated,
            "member_recharge_discount": 1.0,
        }

    @staticmethod
    def action_display_name(action_key: str) -> str:
        key = (action_key or "").strip()
        if not key:
            return "账户变动"
        if key.startswith("drama.agent."):
            slug = key[len("drama.agent.") :].replace("-", " ")
            return f"Drama·{slug}"
        row = BillingService.get_price_row(key)
        if row and row.display_name:
            return row.display_name
        static_labels = {
            "ai.generate.refund": "AI 生成失败退还",
            "signup.bonus": "注册赠送",
            "membership.grant": "会员赠送",
            "recharge.grant": "充值到账",
            "creation.submit": "发起创作",
        }
        if key in static_labels:
            return static_labels[key]
        if key.startswith("ai.generate."):
            slug = key.replace("ai.generate.", "").replace("_", " ")
            return f"AI·{slug}"
        return key

    @staticmethod
    def refund_remark(source_action_key: str) -> str:
        name = BillingService.action_display_name(source_action_key)
        return f"生成失败退还 · {name}"

    @staticmethod
    def ledger_category(*, delta: int, action_key: str, remark: str = "") -> str:
        key = action_key or ""
        if delta > 0:
            if key == "ai.generate.refund" or "生成失败退还" in (remark or ""):
                return "失败退还"
            if key == "membership.grant":
                return "会员赠送"
            if key == "signup.bonus":
                return "注册赠送"
            if key == "recharge.grant":
                return "充值到账"
            return "收入"
        if key.startswith("ai.generate."):
            return "AI 消耗"
        if key.startswith("drama.agent."):
            return "Drama 角色"
        if key == "creation.submit":
            return "发起创作"
        return "消耗"

    @staticmethod
    def format_ledger_description(*, action_key: str, remark: str, delta: int) -> str:
        text = (remark or "").strip()
        if "生成失败退还" in text:
            tail = text
            for sep in ("·", "：", ":"):
                if sep in text:
                    tail = text.split(sep, 1)[-1].strip()
                    break
            if tail.startswith("ai.generate.") or tail.startswith("pipeline."):
                return BillingService.refund_remark(tail)
            return text.replace("：", " · ", 1).replace(":", " · ", 1)
        if text:
            if text == action_key or text.startswith(("ai.generate.", "pipeline.", "creation.")):
                return BillingService.action_display_name(text)
            return text
        return BillingService.action_display_name(action_key)

    @staticmethod
    def list_ledger(user, *, entry_type: str = "", page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        qs = CoinLedger.objects.filter(user=user).order_by("-created_at")
        if entry_type == "income":
            qs = qs.filter(delta__gt=0)
        elif entry_type == "spend":
            qs = qs.filter(delta__lt=0)
        total = qs.count()
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        start = (page - 1) * page_size
        items = []
        for row in qs[start : start + page_size]:
            description = BillingService.format_ledger_description(
                action_key=row.action_key,
                remark=row.remark,
                delta=row.delta,
            )
            items.append(
                {
                    "id": str(row.id),
                    "delta": row.delta,
                    "balance_after": row.balance_after,
                    "entry_type": row.entry_type,
                    "action_key": row.action_key,
                    "remark": row.remark,
                    "description": description,
                    "category": BillingService.ledger_category(
                        delta=row.delta,
                        action_key=row.action_key,
                        remark=row.remark,
                    ),
                    "reference_id": row.reference_id,
                    "created_at": row.created_at,
                }
            )
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
        }

    @staticmethod
    def get_price_row(action_key: str) -> Optional[ActionPricing]:
        return ActionPricing.objects.filter(action_key=action_key, is_active=True).first()

    @staticmethod
    def get_price(action_key: str) -> int:
        row = BillingService.get_price_row(action_key)
        if row:
            return int(row.coin_cost)
        return 0

    @staticmethod
    @transaction.atomic
    def credit(
        user,
        amount: int,
        *,
        action_key: str = "",
        reference_id: str = "",
        remark: str = "",
        entry_type: str = CoinLedger.TYPE_GRANT,
    ) -> UserWallet:
        if amount <= 0:
            raise ValueError("发放数量须大于 0")
        wallet = BillingService.get_or_create_wallet(user)
        if (
            action_key in {"recharge.grant", "membership.grant"}
            and reference_id
            and CoinLedger.objects.filter(
                user=user,
                action_key=action_key,
                reference_id=reference_id,
                delta__gt=0,
            ).exists()
        ):
            logger.warning(
                "忽略重复入账 user=%s action=%s reference=%s",
                user.id,
                action_key,
                reference_id,
            )
            return wallet
        try:
            with transaction.atomic():
                return BillingService._apply_delta(
                    wallet,
                    amount,
                    entry_type=entry_type,
                    action_key=action_key,
                    reference_id=reference_id,
                    remark=remark,
                )
        except IntegrityError:
            logger.warning(
                "忽略并发重复入账 user=%s action=%s reference=%s",
                user.id,
                action_key,
                reference_id,
            )
            wallet.refresh_from_db()
            return wallet

    @staticmethod
    @transaction.atomic
    def reverse_credit(
        user,
        amount: int,
        *,
        action_key: str,
        reference_id: str,
        remark: str = "",
    ) -> UserWallet:
        """冲正已发放创作币；不允许产生负余额。"""
        if amount <= 0:
            raise ValueError("冲正数量须大于 0")
        wallet = BillingService.get_or_create_wallet(user)
        return BillingService._apply_delta(
            wallet,
            -amount,
            entry_type=CoinLedger.TYPE_REFUND,
            action_key=action_key,
            reference_id=reference_id,
            remark=remark,
        )

    @staticmethod
    @transaction.atomic
    def charge(
        user,
        action_key: str,
        *,
        reference_id: str = "",
        remark: str = "",
        coin_cost: Optional[int] = None,
    ) -> Tuple[UserWallet, int]:
        cost = coin_cost if coin_cost is not None else BillingService.get_price(action_key)
        if cost <= 0:
            wallet = BillingService.get_or_create_wallet(user)
            return wallet, wallet.balance

        row = BillingService.get_price_row(action_key)
        if row and row.member_only:
            from apps.membership.services import MembershipService

            ok, msg = MembershipService.check_membership_status(user)
            if not ok:
                raise PermissionDenied(msg or "该功能需有效会员")

        wallet = BillingService.get_or_create_wallet(user)
        if wallet.balance < cost:
            raise InsufficientCoins(
                f"{BillingService.currency_name()}不足，需要 {cost}，当前 {wallet.balance}"
            )
        if reference_id and CoinLedger.objects.filter(
            user=user,
            action_key=action_key,
            reference_id=reference_id,
            delta__lt=0,
        ).exists():
            logger.warning(
                "忽略重复扣费 user=%s action=%s reference=%s",
                user.id,
                action_key,
                reference_id,
            )
            return wallet, wallet.balance
        try:
            with transaction.atomic():
                BillingService._apply_delta(
                    wallet,
                    -cost,
                    entry_type=CoinLedger.TYPE_SPEND,
                    action_key=action_key,
                    reference_id=reference_id,
                    remark=remark or BillingService.action_display_name(action_key),
                )
        except IntegrityError:
            logger.warning(
                "忽略并发重复扣费 user=%s action=%s reference=%s",
                user.id,
                action_key,
                reference_id,
            )
        wallet.refresh_from_db()
        return wallet, wallet.balance

    @staticmethod
    def _apply_delta(
        wallet: UserWallet,
        delta: int,
        *,
        entry_type: str,
        action_key: str = "",
        reference_id: str = "",
        remark: str = "",
    ) -> UserWallet:
        UserWallet.objects.filter(pk=wallet.pk).update(balance=F("balance") + delta)
        wallet.refresh_from_db()
        if wallet.balance < 0:
            UserWallet.objects.filter(pk=wallet.pk).update(balance=F("balance") - delta)
            raise InsufficientCoins(f"{BillingService.currency_name()}不足")
        CoinLedger.objects.create(
            user=wallet.user,
            delta=delta,
            balance_after=wallet.balance,
            entry_type=entry_type,
            action_key=action_key,
            reference_id=reference_id,
            remark=remark,
        )
        return wallet

    @staticmethod
    def ensure_can_create(user) -> None:
        settings_obj = BillingService.site_settings()
        if settings_obj.require_membership_for_creation:
            from apps.membership.services import MembershipService

            ok, msg = MembershipService.check_membership_status(user)
            if not ok:
                raise PermissionDenied(msg or "需有效会员才可创作")

    @staticmethod
    def estimate_auto_pipeline_cost() -> int:
        from apps.skill.drama_pricing import estimate_fast_track_cost

        return estimate_fast_track_cost()

    @staticmethod
    def list_active_pricing() -> List[Dict[str, Any]]:
        return list(
            ActionPricing.objects.filter(is_active=True)
            .order_by("sort_order", "action_key")
            .values("action_key", "display_name", "coin_cost")
        )

    @staticmethod
    def list_field_actions() -> List[Dict[str, Any]]:
        return list(
            ActionPricing.objects.filter(is_active=True, action_key__startswith="ai.generate.")
            .order_by("sort_order", "action_key")
            .values("action_key", "display_name", "coin_cost", "member_only")
        )


def _resolve_billing_user(user_id):
    from django.contrib.auth import get_user_model

    if user_id is None:
        raise ValueError("user_id 不能为空")
    return get_user_model().objects.get(pk=user_id)


def check_and_charge_coins(
    *,
    user_id,
    amount: float | int,
    description: str = "",
    reference_id: str = "",
    action_key: str = "skill.invoke",
) -> Tuple[bool, str]:
    """技能调用配额预扣；供 SkillInvoker / WorkflowEngine 使用。"""
    cost = int(amount)
    if cost <= 0:
        return True, ""

    try:
        user = _resolve_billing_user(user_id)
        BillingService.charge(
            user,
            action_key,
            reference_id=reference_id,
            remark=description or BillingService.action_display_name(action_key),
            coin_cost=cost,
        )
        return True, ""
    except InsufficientCoins as exc:
        return False, str(exc)
    except PermissionDenied as exc:
        return False, str(exc)


def refund_coins(
    *,
    user_id,
    amount: float | int,
    description: str = "",
    reference_id: str = "",
) -> None:
    """技能/节点失败时回补创作币。"""
    cost = int(amount)
    if cost <= 0 or not reference_id:
        return

    user = _resolve_billing_user(user_id)
    if CoinLedger.objects.filter(
        user=user,
        reference_id=reference_id,
        delta__gt=0,
    ).exists():
        logger.warning(
            "忽略重复技能配额回补 user=%s reference=%s",
            user_id,
            reference_id,
        )
        return

    BillingService.credit(
        user,
        cost,
        action_key="ai.generate.refund",
        reference_id=reference_id,
        remark=description or "技能调用失败退还",
        entry_type=CoinLedger.TYPE_REFUND,
    )


