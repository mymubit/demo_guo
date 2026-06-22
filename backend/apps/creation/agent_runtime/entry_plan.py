# -*- coding: utf-8 -*-
"""创作入口 → 推荐 Agent Plan（非 LLM 动态编排）。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

DEFAULT_ENTRY_PLANS: Dict[str, Dict[str, Any]] = {
    "from-scratch": {
        "recommended_agents": ["structure", "character", "outline", "script", "review"],
        "hidden_agents": [],
        "default_params": {},
    },
    "from-outline": {
        "recommended_agents": ["character", "script", "review"],
        "hidden_agents": ["structure", "outline"],
        "default_params": {},
    },
    "from-reference": {
        "recommended_agents": ["structure", "outline", "script", "review"],
        "hidden_agents": [],
        "default_params": {},
    },
    "ip-sequel": {
        "recommended_agents": ["outline", "script", "review"],
        "hidden_agents": ["structure"],
        "default_params": {},
    },
    "novel-adaptation": {
        "recommended_agents": ["script", "review"],
        "hidden_agents": ["structure", "outline", "character"],
        "default_params": {},
    },
}


def _known_agent_ids() -> Set[str]:
    try:
        from apps.agent.definition_service import AgentDefinitionService

        AgentDefinitionService.ensure_defaults()
        return {a.agent_id for a in AgentDefinitionService.active_agents()}
    except Exception:  # noqa: BLE001
        return set()


def _validate_plan_agent_ids(plan: Dict[str, Any]) -> Dict[str, Any]:
    known = _known_agent_ids()
    if not known:
        return plan
    for field in ("recommended_agents", "hidden_agents"):
        for aid in plan.get(field) or []:
            if str(aid) not in known:
                logger.warning("[EntryPlan] 未知 agent_id=%s，请检查 creation-entry-plans 配置", aid)
    return plan


def get_entry_plan(creation_entry: str) -> Dict[str, Any]:
    key = (creation_entry or "from-scratch").strip() or "from-scratch"
    try:
        from apps.skill.models import SkillConfigEntry

        row = SkillConfigEntry.objects.filter(config_key="creation-entry-plans").first()
        if row and isinstance(row.content, dict) and key in row.content:
            plan = row.content[key]
            if isinstance(plan, dict):
                resolved = {
                    "recommended_agents": list(plan.get("recommended_agents") or []),
                    "hidden_agents": list(plan.get("hidden_agents") or []),
                    "default_params": dict(plan.get("default_params") or {}),
                }
                return _validate_plan_agent_ids(resolved)
    except Exception:  # noqa: BLE001
        pass
    return _validate_plan_agent_ids(dict(DEFAULT_ENTRY_PLANS.get(key) or DEFAULT_ENTRY_PLANS["from-scratch"]))


def filter_agents_for_workspace(
    agent_items: List[Dict[str, Any]],
    creation_entry: str,
) -> List[Dict[str, Any]]:
    plan = get_entry_plan(creation_entry)
    hidden = {str(x) for x in plan.get("hidden_agents") or []}
    recommended = [str(x) for x in plan.get("recommended_agents") or []]
    rec_rank = {aid: idx for idx, aid in enumerate(recommended)}
    visible = []
    for item in agent_items:
        aid = str(item.get("agent_id") or "")
        if aid in hidden:
            continue
        enriched = dict(item)
        enriched["entry_recommended"] = aid in rec_rank
        enriched["entry_sort"] = rec_rank.get(aid, 1000 + int(enriched.get("workspace_order") or 0))
        visible.append(enriched)
    visible.sort(key=lambda row: (0 if row.get("entry_recommended") else 1, row.get("entry_sort", 9999)))
    return visible
