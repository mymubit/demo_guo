# -*- coding: utf-8 -*-
"""流水线节点 → Agent 绑定，以及 Agent 的 Prompt / Tier1 解析（只读 Registry）。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from apps.common.agent_term import alias_agent_id
from apps.agent.bootstrap.tier1_sections import AGENT_TIER1_SEED

logger = logging.getLogger(__name__)


def agent_id_for_fusion_node(fusion_node_id: str) -> Optional[str]:
    """fusion_node_id → agent_id，经流水线步骤序号查 Agent Registry。"""
    key = (fusion_node_id or "").strip()
    if not key:
        return None
    try:
        from apps.agent.runtime import agent_for_pipeline_node_index
        from apps.workflow.fusion.registry import FusionNodeRegistry

        for node in FusionNodeRegistry().main_chain_nodes():
            if node.get("fusion_node_id") == key:
                idx = node.get("index")
                if idx is not None:
                    return agent_for_pipeline_node_index(int(idx))
                break
    except Exception as exc:  # noqa: BLE001
        logger.debug("[NodeBinding] fusion_node→agent failed %s: %s", key, exc)
    return None


def agent_id_for_pipeline_index(node_index: int) -> Optional[str]:
    try:
        from apps.agent.runtime import agent_for_pipeline_node_index

        return agent_for_pipeline_node_index(int(node_index))
    except Exception:  # noqa: BLE001
        return None


def get_agent_definition(agent_id: str) -> Dict[str, Any]:
    try:
        from apps.agent.runtime import get_agent

        return dict(get_agent((agent_id or "").strip()) or {})
    except Exception:  # noqa: BLE001
        return {}


def resolve_tier1_sections_for_agent(agent_id: str) -> List[str]:
    aid = (agent_id or "").strip()
    if not aid:
        return []
    agent = get_agent_definition(aid)
    sections = agent.get("tier1_sections")
    if isinstance(sections, list) and sections:
        return [str(s).strip() for s in sections if str(s).strip()]
    return list(AGENT_TIER1_SEED.get(aid) or [])


def resolve_tier1_sections_for_node(fusion_node_id: str) -> List[str]:
    agent_id = agent_id_for_fusion_node(fusion_node_id)
    if agent_id:
        return resolve_tier1_sections_for_agent(agent_id)
    return []


def resolve_prompt_for_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    aid = (agent_id or "").strip()
    if not aid:
        return None
    agent = get_agent_definition(aid)
    prompt = agent.get("prompt")
    if not isinstance(prompt, dict):
        return None
    if not agent.get("prompt_enabled", True):
        return None
    system = str(prompt.get("system") or "")
    user_tpl = str(prompt.get("userTemplate") or prompt.get("user_prompt_tpl") or "")
    constraints = str(prompt.get("constraints") or "")
    if not (system or user_tpl or constraints):
        return None
    return {
        "system": system,
        "userTemplate": user_tpl,
        "constraints": constraints,
    }


def resolve_prompt_for_node(fusion_node_id: str) -> Optional[Dict[str, Any]]:
    agent_id = agent_id_for_fusion_node(fusion_node_id)
    if agent_id:
        return resolve_prompt_for_agent(agent_id)
    return None


def build_prompts_dict_by_agent() -> Dict[str, Any]:
    """供 FusionPromptBuilder：fusion_node_id → prompt。"""
    nodes: Dict[str, Any] = {}
    try:
        from apps.workflow.fusion.registry import FusionNodeRegistry

        for node in FusionNodeRegistry().main_chain_nodes():
            node_id = node.get("fusion_node_id") or ""
            if not node_id:
                continue
            prompt = resolve_prompt_for_node(node_id)
            if prompt:
                nodes[node_id] = prompt
    except Exception as exc:  # noqa: BLE001
        logger.warning("[NodeBinding] build_prompts_dict failed: %s", exc)
    return {"nodes": nodes}


def agent_skill_admin_view(agent_id: str) -> Dict[str, Any]:
    aid = (agent_id or "").strip()
    agent = get_agent_definition(aid)
    prompt = agent.get("prompt") if isinstance(agent.get("prompt"), dict) else {}
    return alias_agent_id({
        "agent_id": aid,
        "tier1_sections": resolve_tier1_sections_for_agent(aid),
        "system_prompt": prompt.get("system") or "",
        "user_prompt_tpl": prompt.get("userTemplate") or prompt.get("user_prompt_tpl") or "",
        "constraints": prompt.get("constraints") or "",
        "prompt_enabled": agent.get("prompt_enabled", True),
        "max_tokens": agent.get("max_tokens"),
        "llm_route_key": agent.get("llm_route_key") or aid,
    })


def pipeline_step_skill_view(fusion_node_id: str) -> Dict[str, Any]:
    agent_id = agent_id_for_fusion_node(fusion_node_id) or ""
    view = agent_skill_admin_view(agent_id) if agent_id else {}
    view["agent_id"] = agent_id
    return alias_agent_id(view)
