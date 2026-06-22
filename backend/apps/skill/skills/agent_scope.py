# -*- coding: utf-8 -*-
"""独立 Agent agent_id ↔ Tier3 fusion node scope 映射。"""
from __future__ import annotations

from typing import Optional

# Tier3 SkillRuleItem / SkillRuleConfig 仍使用 node-* scope_key
AGENT_ID_TO_NODE_SCOPE: dict[str, str] = {
    "brief": "node-1-brief",
    "structure": "node-2-structure",
    "character": "node-3-character",
    "outline": "node-4-outline",
    "script": "node-5-script",
    "review": "node-6-review",
    "polish": "node-7-polish",
}


def node_scope_for_agent(agent_id: str) -> str:
    """返回 Tier3 规则 scope_key；未知 Agent 返回空串（仅加载 global Tier）。"""
    key = (agent_id or "").strip()
    return AGENT_ID_TO_NODE_SCOPE.get(key, "")


def genre_from_project_payload(project_payload: dict) -> str:
    theme = (project_payload or {}).get("theme") or ""
    return str(theme).strip()
