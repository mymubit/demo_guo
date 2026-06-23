# -*- coding: utf-8 -*-
"""
Agent 运行时工具函数 — drama.* 新体系。

旧的 brief/structure/character/outline/script 等硬编码已移除。
现在所有 Agent 统一通过 AgentDefinition 数据库记录管理。
"""
from __future__ import annotations

import logging
from functools import lru_cache
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
    "drama.topic-planner": 103,
    "drama.world-architect": 201,
    "drama.character-designer": 202,
    "drama.plot-architect": 302,
    "drama.script-writer": 401,
    "drama.script-reviewer": 501,
    "drama.quality-reporter": 504,
    "drama.compliance-guard": 801,
    "drama.market-analyst": 106,
    "drama.narrative-engineer": 308,
    "drama.polish-master": 601,
    "drama.production-pack": 701,
}


def action_key_agent_meta(action_key: str) -> Dict[str, Any]:
    """解析计费 action_key 对应的 drama.* agent 元信息。"""
    key = (action_key or "").strip()
    if key.startswith("drama.agent."):
        slug = key[len("drama.agent.") :]
        return {"agent_id": f"drama.{slug}", "billing_scope": "drama"}
    if key.startswith("drama."):
        return {"agent_id": key, "billing_scope": "drama"}
    return {}


def primary_output_artifact(agent_id: str) -> str:
    """推断 Agent 主输出产物键。"""
    agent = get_agent(agent_id)
    if agent:
        outputs = agent.get("outputs") or []
        if outputs:
            return str(outputs[0])
    if agent_id.startswith("drama."):
        try:
            from apps.agent.definition_service import AgentDefinitionService

            row = AgentDefinitionService.get(agent_id)
            if row and isinstance(row.output_contract, dict):
                artifacts = row.output_contract.get("artifacts") or []
                if artifacts:
                    return str(artifacts[0])
        except Exception:  # noqa: BLE001
            pass
    return ""


def workspace_index_for_agent(agent_id: str) -> int:
    """获取 Agent 在工作台中的排序位置。"""
    return DRAMA_WORKSPACE_ORDER.get(agent_id, 999)


def get_agent_registry() -> Dict[str, Any]:
    """
    从数据库获取所有 drama.* Agent 的运行时描述。
    结果按 workspace_order 排序。
    """
    return _load_agent_registry()


@lru_cache(maxsize=1)
def _load_agent_registry() -> Dict[str, Any]:
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


get_agent_registry.cache_clear = _load_agent_registry.cache_clear  # type: ignore[attr-defined]


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
