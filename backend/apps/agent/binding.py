# -*- coding: utf-8 -*-
"""
Agent 绑定工具 — drama.* 新体系。

旧的 FusionNodeRegistry / FusionPipelineNode 依赖已移除。
现在直接通过 AgentDefinition 数据库查询 drama.* 角色。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from apps.agent.bootstrap.tier1_sections import AGENT_TIER1_SEED

logger = logging.getLogger(__name__)


def agent_id_for_fusion_node(fusion_node_id: str) -> Optional[str]:
    """
    fusion_node_id → drama.* agent_id 映射。

    旧的 FusionNodeRegistry 已废弃。
    此函数保留接口兼容性，返回 None（旧节点不再有对应 agent）。
    """
    logger.debug("[Binding] agent_id_for_fusion_node(%s) - 旧节点系统已废弃", fusion_node_id)
    return None


def resolve_tier1_sections_for_agent(agent_id: str) -> List[str]:
    """获取 drama.* Agent 的 Tier1 知识区块列表。"""
    return AGENT_TIER1_SEED.get(agent_id, [])


def resolve_tier1_sections_for_node(node_id: str) -> List[str]:
    """通过节点 ID 获取 Tier1 区块（保留接口兼容性，返回空列表）。"""
    return []


def get_agent_prompt_version(agent_id: str) -> Optional[Any]:
    """获取 drama.* Agent 的当前活跃 Prompt 版本。"""
    try:
        from apps.agent.models import AgentDefinition, AgentPromptVersion

        agent = AgentDefinition.objects.filter(
            agent_id=agent_id,
            is_enabled=True,
        ).first()
        if not agent:
            return None

        return AgentPromptVersion.objects.filter(
            agent=agent,
            is_active=True,
        ).first()

    except Exception as exc:  # noqa: BLE001
        logger.warning("[Binding] get_agent_prompt_version(%s) failed: %s", agent_id, exc)
        return None


def resolve_knowledge_bindings(agent_id: str) -> List[Dict[str, Any]]:
    """获取 drama.* Agent 的知识绑定列表（from AgentKnowledgeBinding）。"""
    try:
        from apps.agent.models import AgentDefinition, AgentKnowledgeBinding

        agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
        if not agent:
            return []

        bindings = AgentKnowledgeBinding.objects.filter(
            agent=agent,
            is_active=True,
        ).select_related("knowledge_item").order_by("sort_order")

        return [
            {
                "id": str(b.id),
                "knowledge_item_id": str(b.knowledge_item_id),
                "injection_policy": b.injection_policy,
                "sort_order": b.sort_order,
            }
            for b in bindings
        ]

    except Exception as exc:  # noqa: BLE001
        logger.warning("[Binding] resolve_knowledge_bindings(%s) failed: %s", agent_id, exc)
        return []
