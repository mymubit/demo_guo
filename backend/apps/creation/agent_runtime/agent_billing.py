# -*- coding: utf-8 -*-
"""独立 Agent 计费 — 对齐 pipeline.node.* 定价（skill-agent/41 §6）。"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.core.exceptions import PermissionDenied

from apps.agent.runtime import workspace_index_for_agent
from apps.billing.services import BillingService, InsufficientCoins

logger = logging.getLogger(__name__)

# 无 workspace_index 的 Agent 映射到原 Fusion 节点定价
_AGENT_NODE_FALLBACK: Dict[str, int] = {
    "review": 6,
    "score": 7,
    "polish": 5,
    "marketing": 6,
    "insight": 7,
}


def agent_action_key(agent_id: str) -> str:
    node_index = workspace_index_for_agent(agent_id)
    if node_index:
        return BillingService.node_action_key(node_index)
    fallback = _AGENT_NODE_FALLBACK.get(str(agent_id or "").strip())
    if fallback:
        return BillingService.node_action_key(fallback)
    return f"creation.agent.{agent_id}"


def resolve_coin_cost(agent_id: str, params: Optional[Dict[str, Any]] = None) -> int:
    """单次 run/stream 会话扣费（script 续写暂按单次节点价，不按集数倍增）。"""
    _ = params
    key = agent_action_key(agent_id)
    cost = BillingService.get_price(key)
    if cost > 0:
        return cost
    if key.startswith("pipeline.node."):
        return 0
    return BillingService.get_price("pipeline.node.6") or 10


def billing_preview(agent_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    action_key = agent_action_key(agent_id)
    return {
        "action_key": action_key,
        "coin_cost": resolve_coin_cost(agent_id, params),
        "display_name": BillingService.action_display_name(action_key),
        "currency_name": BillingService.currency_name(),
    }


def ensure_agent_chargeable(user, agent_id: str, params: Optional[Dict[str, Any]] = None) -> None:
    action_key = agent_action_key(agent_id)
    cost = resolve_coin_cost(agent_id, params)
    row = BillingService.get_price_row(action_key)
    if row and row.member_only:
        from apps.membership.services import MembershipService

        ok, msg = MembershipService.check_membership_status(user)
        if not ok:
            raise PermissionDenied(msg or "该功能需有效会员")
    if cost <= 0:
        return
    balance = BillingService.get_balance(user)
    if balance < cost:
        raise InsufficientCoins(
            f"{BillingService.currency_name()}不足，需要 {cost}，当前 {balance}"
        )


def charge_agent_run(
    user,
    agent_id: str,
    *,
    run_id: str,
    params: Optional[Dict[str, Any]] = None,
) -> int:
    """按 run_id 幂等扣费；返回实际扣除币数。"""
    action_key = agent_action_key(agent_id)
    cost = resolve_coin_cost(agent_id, params)
    if cost <= 0:
        return 0
    display = BillingService.action_display_name(action_key)
    _, balance = BillingService.charge(
        user,
        action_key,
        reference_id=str(run_id),
        remark=display,
        coin_cost=cost,
    )
    logger.info(
        "Agent 扣费 agent=%s run=%s cost=%s balance=%s",
        agent_id,
        run_id,
        cost,
        balance,
    )
    return cost


def refund_agent_run(user, agent_id: str, *, run_id: str) -> int:
    """执行失败时按 run_id 回补（幂等）。"""
    action_key = agent_action_key(agent_id)
    cost = resolve_coin_cost(agent_id)
    if cost <= 0:
        return 0
    from apps.billing.models import CoinLedger

    if not CoinLedger.objects.filter(
        user=user,
        action_key=action_key,
        reference_id=str(run_id),
        delta__lt=0,
    ).exists():
        return 0
    if CoinLedger.objects.filter(
        user=user,
        action_key=action_key,
        reference_id=str(run_id),
        delta__gt=0,
    ).exists():
        return 0
    BillingService.credit(
        user,
        cost,
        action_key=action_key,
        reference_id=str(run_id),
        remark=BillingService.refund_remark(action_key),
    )
    logger.info("Agent 失败回补 agent=%s run=%s cost=%s", agent_id, run_id, cost)
    return cost
