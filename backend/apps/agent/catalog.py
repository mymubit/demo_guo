# -*- coding: utf-8 -*-
"""Agent 中心 — C 端目录与主链展示增强。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from apps.agent.runtime import (
    agent_for_workspace_index,
    get_agent,
    get_agent_registry,
    post_script_append_agents,
    post_script_chain,
    post_script_effective_chain,
    polish_max_rounds,
)


def enrich_portal_chain_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """主链节点附加 Agent SSOT 元数据（C 端展示）。"""
    idx = item.get("index")
    aid = agent_for_workspace_index(int(idx)) if idx is not None else None
    if not aid:
        return dict(item)
    agent = get_agent(aid) or {}
    out = dict(item)
    out["agent_id"] = aid
    out["agent_name"] = agent.get("name") or ""
    out["agent_name_zh"] = agent.get("name_zh") or out.get("name") or ""
    if agent.get("description"):
        out["description"] = agent["description"]
    out["sub_skill_count"] = len(agent.get("sub_skills") or [])
    out["output_artifacts"] = agent.get("outputs") or []
    return out


def enrich_portal_main_chain(
    chain: List[Dict[str, Any]],
    pack_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    from apps.workflow.services.flow_graph_service import FlowGraphPlanService

    enriched = [enrich_portal_chain_item(item) for item in chain]
    return FlowGraphPlanService.enrich_portal_chain(enriched, pack_id=pack_id)


def portal_agent_catalog() -> Dict[str, Any]:
    """C 端 Agent 目录（registry v2 SSOT）。"""
    reg = get_agent_registry()
    meta = reg.get("_meta") or {}
    workspace: List[Dict[str, Any]] = []
    post_script: List[Dict[str, Any]] = []
    auxiliary: List[Dict[str, Any]] = []

    for agent in reg.get("agents") or []:
        if not isinstance(agent, dict):
            continue
        sub_skills = []
        for skill in agent.get("sub_skills") or []:
            if not isinstance(skill, dict):
                continue
            sub_skills.append(
                {
                    "id": skill.get("id"),
                    "type": skill.get("type"),
                    "description": skill.get("description"),
                    "cli": skill.get("cli"),
                }
            )
        entry = {
            "id": agent.get("id"),
            "name": agent.get("name"),
            "name_zh": agent.get("name_zh"),
            "description": agent.get("description"),
            "workspace_index": agent.get("workspace_index"),
            "inputs": agent.get("inputs") or [],
            "outputs": agent.get("outputs") or [],
            "sub_skill_count": len(sub_skills),
            "sub_skills": sub_skills,
            "absorbs_legacy": [
                x.get("id") if isinstance(x, dict) else x
                for x in (agent.get("absorbs_legacy") or [])
            ],
        }
        if agent.get("workspace_index"):
            workspace.append(entry)
        elif agent.get("id") in post_script_effective_chain():
            post_script.append(entry)
        else:
            auxiliary.append(entry)

    workspace.sort(key=lambda x: int(x.get("workspace_index") or 0))
    return {
        "version": meta.get("version") or "2.0.0",
        "orchestrator": reg.get("orchestrator") or {},
        "workspaceAgents": workspace,
        "postScriptAgents": post_script,
        "auxiliaryAgents": auxiliary,
        "post_script_chain": post_script_chain(),
        "post_script_append_agents": post_script_append_agents(),
        "polish_max_rounds": polish_max_rounds(),
        "decisions": reg.get("decisions") or {},
    }
