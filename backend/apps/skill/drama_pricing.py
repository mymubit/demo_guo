# -*- coding: utf-8 -*-
"""Drama 快速通道公开定价（替代 legacy WorkflowPipelineService）。"""
from __future__ import annotations

from typing import Any, Dict, List

from apps.agent.runtime import DRAMA_FAST_TRACK_AGENT_IDS
from apps.creation.agent_runtime.agent_billing import agent_action_key


def _agent_display_name(agent_id: str) -> str:
    try:
        from apps.agent.definition_service import AgentDefinitionService

        row = AgentDefinitionService.get(agent_id)
        if row:
            return (row.name_zh or row.name or agent_id)[:64]
    except Exception:  # noqa: BLE001
        pass
    return agent_id.split(".")[-1].replace("-", " ").title()


def _agent_coin_cost(agent_id: str) -> int:
    from apps.billing.services import BillingService

    return BillingService.get_price(agent_action_key(agent_id))


def list_public_drama_roles() -> List[Dict[str, Any]]:
    """C 端计费目录：Drama 快速通道角色列表。"""
    rows: List[Dict[str, Any]] = []
    for idx, agent_id in enumerate(DRAMA_FAST_TRACK_AGENT_IDS, start=1):
        rows.append(
            {
                "index": idx,
                "agent_id": agent_id,
                "name": _agent_display_name(agent_id),
                "coin_cost": _agent_coin_cost(agent_id),
            }
        )
    return rows


def estimate_fast_track_cost() -> int:
    """估算快速通道全流程消耗（提交费 + 各角色）。"""
    from apps.billing.services import BillingService

    total = BillingService.get_price("creation.submit")
    for row in list_public_drama_roles():
        total += int(row.get("coin_cost") or 0)
    return total
