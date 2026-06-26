# -*- coding: utf-8
"""
创作入口规划 — drama.* 新体系。

编排顺序来自 drama-skills/orchestration/*.yaml（Git SSOT）。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DramaEntryPlan:
    """drama.* 创作入口规划。"""

    @classmethod
    def resolve(cls, track_mode: str = "fast", entry_type: str = "from-scratch") -> Dict[str, Any]:
        from apps.drama.skills_registry import get_entry_plan

        if entry_type in ("from-novel", "novel-adaptation"):
            plan = get_entry_plan("ip_adapt")
        elif track_mode == "expert":
            plan = get_entry_plan("expert")
        else:
            plan = get_entry_plan("fast")

        if plan.get("recommended_agents") is not None:
            return {
                "entry_type": plan.get("entry_type") or "fast_track",
                "label": plan.get("label") or "快速通道",
                "description": plan.get("description") or "",
                "recommended_agents": list(plan.get("recommended_agents") or []),
                "optional_agents": list(plan.get("optional_agents") or []),
            }
        return {
            "entry_type": plan.get("entry_type") or "expert_track",
            "label": plan.get("label") or "专家通道",
            "description": plan.get("description") or "",
            "phases": plan.get("phases") or [],
        }

    @classmethod
    def list_agent_ids(cls, track_mode: str = "fast", entry_type: str = "from-scratch") -> list[str]:
        plan = cls.resolve(track_mode=track_mode, entry_type=entry_type)
        if plan.get("recommended_agents"):
            return list(plan["recommended_agents"])
        agents: list[str] = []
        for phase in plan.get("phases") or []:
            agents.extend(phase.get("agents") or [])
        return agents


def get_entry_plan(entry_type: str = "from-scratch", *, track_mode: str = "fast") -> Dict[str, Any]:
    """读取创作入口计划（DB 覆盖 + drama-skills orchestration 默认）。"""
    from apps.agent.definition_service import AgentDefinitionService
    from apps.skill.models import SkillConfigEntry

    plan = dict(DramaEntryPlan.resolve(track_mode=track_mode, entry_type=entry_type))
    try:
        row = SkillConfigEntry.objects.filter(config_key="creation-entry-plans").first()
        content = (row.content if row else None) or {}
        override = content.get(entry_type) if isinstance(content, dict) else None
        if isinstance(override, dict):
            if override.get("recommended_agents") is not None:
                plan["recommended_agents"] = list(override["recommended_agents"])
            if override.get("hidden_agents") is not None:
                plan["hidden_agents"] = list(override["hidden_agents"])
            known = {a.agent_id for a in AgentDefinitionService.active_agents()}
            for agent_id in plan.get("recommended_agents") or []:
                if agent_id not in known:
                    logger.warning("[EntryPlan] unknown agent in plan %s: %s", entry_type, agent_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[EntryPlan] load override failed: %s", exc)
    return plan


def filter_agents_for_workspace(agent_items: List[Dict[str, Any]], entry_type: str) -> List[Dict[str, Any]]:
    """按入口计划 hidden_agents 过滤工作台展示。"""
    plan = get_entry_plan(entry_type)
    hidden = set(plan.get("hidden_agents") or [])
    if not hidden:
        return agent_items
    return [item for item in agent_items if item.get("agent_id") not in hidden]
