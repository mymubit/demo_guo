# -*- coding: utf-8 -*-
"""
创作入口规划 — drama.* 新体系。

根据用户的创作入口类型，推荐对应的 drama.* 角色执行顺序。
"""
from __future__ import annotations

from typing import Any, Dict, List

import logging

from apps.agent.runtime import DRAMA_FAST_TRACK_AGENT_IDS

logger = logging.getLogger(__name__)


class DramaEntryPlan:
    """
    drama.* 创作入口规划。

    根据 track_mode（fast/expert）和创作起点类型，
    决定推荐的角色执行顺序。
    """

    # 快速通道：8个核心角色
    FAST_TRACK_PLAN = {
        "entry_type": "fast_track",
        "label": "快速通道",
        "description": "8个核心角色，适合初次创作和快速验证",
        "recommended_agents": DRAMA_FAST_TRACK_AGENT_IDS,
        "optional_agents": [],
    }

    # 专家通道：12个可见角色，按部门分阶段
    EXPERT_TRACK_PLAN = {
        "entry_type": "expert_track",
        "label": "专家通道",
        "description": "12个可见角色（8核心+4复合），适合商业精品项目",
        "phases": [
            {
                "phase": "strategy",
                "label": "战略选题",
                "agents": ["drama.topic-planner", "drama.market-analyst"],
            },
            {
                "phase": "worldbuilding",
                "label": "世界构建",
                "agents": ["drama.world-architect", "drama.character-designer"],
            },
            {
                "phase": "plot_design",
                "label": "剧情引擎",
                "agents": ["drama.plot-architect", "drama.narrative-engineer"],
            },
            {
                "phase": "writing",
                "label": "创作执行",
                "agents": ["drama.script-writer"],
            },
            {
                "phase": "review",
                "label": "评审质控",
                "agents": ["drama.script-reviewer", "drama.quality-reporter"],
            },
            {
                "phase": "polish",
                "label": "修改润色",
                "agents": ["drama.polish-master"],
            },
            {
                "phase": "production",
                "label": "制作宣发",
                "agents": ["drama.production-pack"],
            },
            {
                "phase": "compliance",
                "label": "合规交付",
                "agents": ["drama.compliance-guard"],
            },
        ],
    }

    # IP改编专用入口
    IP_ADAPT_PLAN = {
        "entry_type": "ip_adapt",
        "label": "IP改编",
        "description": "小说/原著改编专用通道",
        "recommended_agents": [
            "drama.topic-planner",
            "drama.world-architect",
            "drama.character-designer",
            "drama.plot-architect",
            "drama.script-writer",
            "drama.script-reviewer",
            "drama.quality-reporter",
            "drama.compliance-guard",
            "drama.narrative-engineer",
            "drama.polish-master",
            "drama.production-pack",
        ],
    }

    @classmethod
    def resolve(cls, track_mode: str = "fast", entry_type: str = "from-scratch") -> Dict[str, Any]:
        """
        根据创作模式和入口类型获取推荐的 Agent 执行计划。

        参数：
        - track_mode: "fast" | "expert"
        - entry_type: "from-scratch" | "from-novel" | "from-outline"
        """
        if entry_type in ("from-novel", "novel-adaptation"):
            return cls.IP_ADAPT_PLAN

        if track_mode == "expert":
            return cls.EXPERT_TRACK_PLAN

        return cls.FAST_TRACK_PLAN

    @classmethod
    def list_agent_ids(cls, track_mode: str = "fast", entry_type: str = "from-scratch") -> list[str]:
        """返回当前轨道下的全部 agent_id 有序列表。"""
        plan = cls.resolve(track_mode=track_mode, entry_type=entry_type)
        if plan.get("recommended_agents"):
            return list(plan["recommended_agents"])
        agents: list[str] = []
        for phase in plan.get("phases") or []:
            agents.extend(phase.get("agents") or [])
        return agents


def get_entry_plan(entry_type: str = "from-scratch", *, track_mode: str = "fast") -> Dict[str, Any]:
    """读取创作入口计划（DB 覆盖 + drama 默认）。"""
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
