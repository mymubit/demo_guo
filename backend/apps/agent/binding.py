# -*- coding: utf-8 -*-
"""
Agent 绑定工具 — drama.* 体系。

直接通过 AgentDefinition 数据库查询 drama.* 角色。
旧的 FusionNodeRegistry 已完全移除。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from apps.agent.bootstrap.tier1_sections import AGENT_TIER1_SEED

logger = logging.getLogger(__name__)


def resolve_tier1_sections_for_agent(agent_id: str) -> List[str]:
    """获取 drama.* Agent 的 Tier1 知识区块列表。"""
    return AGENT_TIER1_SEED.get(agent_id, [])


def get_agent_prompt_version(agent_id: str) -> Optional[Any]:
    """获取 drama.* Agent 的当前活跃 Prompt 版本。"""
    try:
        from apps.agent.models import AgentDefinition, AgentPromptVersion

        agent = AgentDefinition.objects.filter(agent_id=agent_id, is_enabled=True).first()
        if not agent:
            return None
        return AgentPromptVersion.objects.filter(agent=agent, is_active=True).first()

    except Exception as exc:  # noqa: BLE001
        logger.warning("[Binding] get_agent_prompt_version(%s) failed: %s", agent_id, exc)
        return None


def resolve_knowledge_bindings(agent_id: str) -> List[Dict[str, Any]]:
    """获取 drama.* Agent 的知识绑定列表。"""
    try:
        from apps.agent.models import AgentDefinition, AgentKnowledgeBinding

        agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
        if not agent:
            return []

        return [
            {
                "id": str(b.id),
                "knowledge_item_id": str(b.knowledge_item_id),
                "injection_policy": b.injection_policy,
                "sort_order": b.sort_order,
            }
            for b in AgentKnowledgeBinding.objects.filter(
                agent=agent, is_active=True,
            ).select_related("knowledge_item").order_by("sort_order")
        ]

    except Exception as exc:  # noqa: BLE001
        logger.warning("[Binding] resolve_knowledge_bindings(%s) failed: %s", agent_id, exc)
        return []
