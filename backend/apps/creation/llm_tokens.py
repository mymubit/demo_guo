# -*- coding: utf-8 -*-
"""各 Agent 单次 LLM 调用的 max_tokens — 仅读数据库。"""
from __future__ import annotations

from typing import Optional

from apps.agent.routes import AgentLlmRouteService


def resolve_agent_max_tokens(
    key: str,
    *,
    override: Optional[int] = None,
    node_id: Optional[str] = None,
) -> int:
    if override is not None:
        return max(256, int(override))
    if node_id:
        node_tokens = AgentLlmRouteService.resolve_node_max_tokens(node_id)
        if node_tokens:
            return node_tokens
    db_tokens = AgentLlmRouteService.resolve_max_tokens(key)
    if db_tokens is not None:
        return db_tokens
    from django.conf import settings

    fallback = int(getattr(settings, "FUSION_LLM_MAX_TOKENS", 6000) or 6000)
    return max(256, fallback)
