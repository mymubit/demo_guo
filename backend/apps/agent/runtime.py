# -*- coding: utf-8 -*-
"""
Agent 运行时工具函数 — drama.* 新体系。

旧的 brief/structure/character/outline/script 等硬编码已移除。
现在所有 Agent 统一通过 AgentDefinition 数据库记录管理。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# drama.* 快速通道角色（workspace_order 决定排序）
DRAMA_FAST_TRACK_AGENT_IDS = [
    "drama.topic-planner",
    "drama.world-architect",
    "drama.character-designer",
    "drama.plot-architect",
    "drama.script-writer",
    "drama.script-reviewer",
    "drama.quality-reporter",
    "drama.compliance-guard",
]

# drama.* 角色按 workspace_order 的顺序（用于进度计算）
DRAMA_WORKSPACE_ORDER = {
    "drama.market-radar": 101,
    "drama.formula-analyst": 102,
    "drama.topic-planner": 103,
    "drama.project-reviewer": 104,
    "drama.lapian-analyst": 105,
    "drama.world-architect": 201,
    "drama.character-designer": 202,
    "drama.dream-analyst": 203,
    "drama.emotion-architect": 301,
    "drama.plot-architect": 302,
    "drama.hook-designer": 303,
    "drama.conflict-engine": 304,
    "drama.reversal-master": 305,
    "drama.rhythm-designer": 306,
    "drama.psychology-architect": 307,
    "drama.script-writer": 401,
    "drama.dialogue-expert": 402,
    "drama.scene-director": 403,
    "drama.ip-adapter": 404,
    "drama.script-reviewer": 501,
    "drama.reader-reviewer": 502,
    "drama.emotion-auditor": 503,
    "drama.quality-reporter": 504,
    "drama.script-editor": 601,
    "drama.pacing-optimizer": 602,
    "drama.formatter": 603,
    "drama.word-governor": 604,
    "drama.style-guardian": 605,
    "drama.visual-producer": 701,
    "drama.storyboard-director": 702,
    "drama.post-processor": 703,
    "drama.marketing-officer": 704,
    "drama.compliance-guard": 801,
    "drama.delivery-packer": 802,
    "drama.evolution-analyst": 803,
}


def workspace_index_for_agent(agent_id: str) -> int:
    """获取 Agent 在工作台中的排序位置。"""
    return DRAMA_WORKSPACE_ORDER.get(agent_id, 999)


def get_agent_registry() -> Dict[str, Any]:
    """
    从数据库获取所有 drama.* Agent 的运行时描述。
    结果按 workspace_order 排序。
    """
    try:
        from apps.agent.models import AgentDefinition
        agents = AgentDefinition.objects.filter(
            category="drama_skills",
            is_enabled=True,
            lifecycle_status=AgentDefinition.LifecycleStatus.ACTIVE,
        ).order_by("workspace_order")

        return {
            "_meta": {"version": "drama-skills-v3.0"},
            "orchestrator": {"runtime": "scriptforge-drama"},
            "agents": [
                {
                    "id": a.agent_id,
                    "name": a.name,
                    "name_zh": a.name_zh,
                    "workspace_order": a.workspace_order,
                    "is_fast_track": a.agent_id in DRAMA_FAST_TRACK_AGENT_IDS,
                    "dept": (a.ui_schema or {}).get("dept", ""),
                    "outputs": (a.output_contract or {}).get("artifacts", []),
                }
                for a in agents
            ],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("[drama runtime] get_agent_registry failed: %s", exc)
        return {"_meta": {"version": "drama-skills-v3.0"}, "agents": []}


def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """按 agent_id 获取单个 Agent 运行时信息。"""
    try:
        from apps.agent.models import AgentDefinition
        agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
        if not agent:
            return None
        return {
            "id": agent.agent_id,
            "name": agent.name,
            "name_zh": agent.name_zh,
            "workspace_order": agent.workspace_order,
            "outputs": (agent.output_contract or {}).get("artifacts", []),
            "input_contract": agent.input_contract,
            "output_contract": agent.output_contract,
            "runtime_policy": agent.runtime_policy,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("[drama runtime] get_agent(%s) failed: %s", agent_id, exc)
        return None
