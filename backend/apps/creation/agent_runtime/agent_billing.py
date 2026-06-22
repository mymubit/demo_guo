# -*- coding: utf-8 -*-
"""
Agent 计费 — drama.* 新体系。

旧的 brief/structure/outline/script/review/score 等 agent 计费已移除。
现在按 drama.* agent_id 直接查 Coin 消耗等级。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)

# drama.* 角色 Coin 消耗等级
DRAMA_AGENT_COIN_COST: Dict[str, int] = {
    # 战略选题部（轻量分析）
    "drama.market-radar": 2,
    "drama.formula-analyst": 2,
    "drama.topic-planner": 3,
    "drama.project-reviewer": 2,
    "drama.lapian-analyst": 5,
    # 世界构建部
    "drama.world-architect": 4,
    "drama.character-designer": 5,
    "drama.dream-analyst": 2,
    # 剧情引擎部
    "drama.emotion-architect": 3,
    "drama.plot-architect": 8,
    "drama.hook-designer": 3,
    "drama.conflict-engine": 3,
    "drama.reversal-master": 3,
    "drama.rhythm-designer": 4,
    "drama.psychology-architect": 3,
    # 创作执行部（核心高消耗）
    "drama.script-writer": 15,
    "drama.dialogue-expert": 8,
    "drama.scene-director": 4,
    "drama.ip-adapter": 10,
    # 评审质控部
    "drama.script-reviewer": 5,
    "drama.reader-reviewer": 4,
    "drama.emotion-auditor": 4,
    "drama.quality-reporter": 6,
    # 修改润色部
    "drama.script-editor": 8,
    "drama.pacing-optimizer": 4,
    "drama.formatter": 2,
    "drama.word-governor": 2,
    "drama.style-guardian": 4,
    # 制作宣发部
    "drama.visual-producer": 5,
    "drama.storyboard-director": 6,
    "drama.post-processor": 4,
    "drama.marketing-officer": 4,
    # 合规总编室
    "drama.compliance-guard": 6,
    "drama.delivery-packer": 3,
    "drama.evolution-analyst": 4,
}

DEFAULT_COIN_COST = 5


def get_agent_coin_cost(agent_id: str) -> int:
    """获取指定 drama.* Agent 的 Coin 消耗量。"""
    return DRAMA_AGENT_COIN_COST.get(agent_id, DEFAULT_COIN_COST)


def agent_action_key(agent_id: str) -> str:
    """将 drama.* agent_id 转换为计费 action key。"""
    if agent_id.startswith("drama."):
        return f"drama.agent.{agent_id[6:]}"  # drama.agent.script-writer
    return f"creation.agent.{agent_id}"


def resolve_coin_cost(agent_id: str, params: Optional[Dict[str, Any]] = None) -> int:
    """获取单次执行的 Coin 消耗量（优先查 ActionPricing 数据库）。"""
    _ = params
    key = agent_action_key(agent_id)
    try:
        from apps.billing.services import BillingService
        cost = BillingService.get_price(key)
        if cost > 0:
            return cost
    except Exception:  # noqa: BLE001
        pass
    return get_agent_coin_cost(agent_id)


def billing_preview(agent_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """获取计费预览信息。"""
    try:
        from apps.billing.services import BillingService
        action_key = agent_action_key(agent_id)
        return {
            "action_key": action_key,
            "coin_cost": resolve_coin_cost(agent_id, params),
            "display_name": BillingService.action_display_name(action_key),
            "currency_name": BillingService.currency_name(),
        }
    except Exception:  # noqa: BLE001
        return {
            "action_key": agent_action_key(agent_id),
            "coin_cost": get_agent_coin_cost(agent_id),
            "display_name": agent_id,
            "currency_name": "Coin",
        }


def ensure_agent_chargeable(user, agent_id: str, params: Optional[Dict[str, Any]] = None) -> None:
    """检查用户余额是否足够执行该角色（不足时抛 InsufficientCoins）。"""
    cost = resolve_coin_cost(agent_id, params)
    if cost <= 0:
        return
    try:
        from apps.billing.services import BillingService, InsufficientCoins
        balance = BillingService.get_balance(user)
        if balance < cost:
            raise InsufficientCoins(
                f"Coin 不足，需要 {cost}，当前 {balance}"
            )
    except ImportError:
        pass


def charge_agent_run(
    user,
    agent_id: str,
    *,
    run_id: str,
    params: Optional[Dict[str, Any]] = None,
) -> int:
    """执行扣费（幂等：同一 run_id 不重复扣）。"""
    action_key = agent_action_key(agent_id)
    cost = resolve_coin_cost(agent_id, params)
    if cost <= 0:
        return 0
    try:
        from apps.billing.services import BillingService
        _, balance = BillingService.charge(
            user,
            action_key,
            reference_id=str(run_id),
            remark=f"drama角色执行: {agent_id}",
            coin_cost=cost,
        )
        logger.info(
            "[AgentBilling] 扣费 agent=%s run=%s cost=%s balance=%s",
            agent_id, run_id, cost, balance,
        )
        return cost
    except Exception as exc:  # noqa: BLE001
        logger.warning("[AgentBilling] 扣费失败 agent=%s: %s", agent_id, exc)
        return 0


def refund_agent_run(user, agent_id: str, *, run_id: str) -> int:
    """执行失败时回补（幂等）。"""
    action_key = agent_action_key(agent_id)
    cost = resolve_coin_cost(agent_id)
    if cost <= 0:
        return 0
    try:
        from apps.billing.models import CoinLedger
        from apps.billing.services import BillingService

        charged = CoinLedger.objects.filter(
            user=user, action_key=action_key, reference_id=str(run_id), delta__lt=0,
        ).exists()
        if not charged:
            return 0
        refunded = CoinLedger.objects.filter(
            user=user, action_key=action_key, reference_id=str(run_id), delta__gt=0,
        ).exists()
        if refunded:
            return 0

        BillingService.credit(
            user, cost,
            action_key=action_key,
            reference_id=str(run_id),
            remark=f"drama角色失败回补: {agent_id}",
        )
        logger.info("[AgentBilling] 回补 agent=%s run=%s cost=%s", agent_id, run_id, cost)
        return cost
    except Exception as exc:  # noqa: BLE001
        logger.warning("[AgentBilling] 回补失败 agent=%s: %s", agent_id, exc)
        return 0
