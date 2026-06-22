# -*- coding: utf-8 -*-
"""
Agent Registry — drama.* 新体系。

提供 Agent 注册表的内存缓存（运行时只读）。
数据来源：AgentDefinition 数据库表（由 seed_drama_skills 种入）。
旧的 builtin_agent（brief/structure/etc）已移除。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_REGISTRY_CACHE: Optional[Dict[str, Any]] = None


class AgentRegistryConfigService:
    """Agent 注册表服务（从 AgentDefinition 数据库加载 drama.* 角色）。"""

    @classmethod
    def get_registry(cls) -> Dict[str, Any]:
        """获取完整的 drama.* Agent 注册表（带缓存）。"""
        global _REGISTRY_CACHE
        if _REGISTRY_CACHE is not None:
            return _REGISTRY_CACHE

        from apps.agent.runtime import get_agent_registry
        _REGISTRY_CACHE = get_agent_registry()
        return _REGISTRY_CACHE

    @classmethod
    def clear_cache(cls) -> None:
        """清除注册表缓存（修改 Agent 配置后调用）。"""
        global _REGISTRY_CACHE
        _REGISTRY_CACHE = None

    @classmethod
    def get_agent(cls, agent_id: str) -> Optional[Dict[str, Any]]:
        """按 agent_id 获取 Agent 信息。"""
        registry = cls.get_registry()
        for agent in registry.get("agents", []):
            if agent.get("id") == agent_id:
                return agent
        return None
