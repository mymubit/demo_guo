# -*- coding: utf-8 -*-
"""
Agent Registry — drama.* 新体系。

提供 Agent 注册表的内存缓存（运行时只读）。
数据来源：AgentDefinition 数据库表（由 seed_drama_skills 种入）。
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

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
        try:
            from apps.agent.runtime import get_agent_registry

            get_agent_registry.cache_clear()
        except Exception:  # noqa: BLE001
            pass

    @classmethod
    def get_agent(cls, agent_id: str) -> Optional[Dict[str, Any]]:
        """按 agent_id 获取 Agent 信息。"""
        registry = cls.get_registry()
        for agent in registry.get("agents", []):
            if agent.get("id") == agent_id:
                return agent
        return None

    @classmethod
    def admin_payload(cls) -> Dict[str, Any]:
        """Admin 只读归档 payload（registry v2 已下线，数据来自 AgentDefinition）。"""
        from apps.agent.bootstrap.tier1_sections import (
            DEFAULT_TIER1_SECTIONS_BY_AGENT,
            tier1_section_catalog_detail,
        )

        registry = cls.get_registry()
        section_keys = sorted(
            {
                key
                for sections in DEFAULT_TIER1_SECTIONS_BY_AGENT.values()
                for key in (sections or [])
            }
        )
        return {
            "source": "drama_definitions",
            "registry": registry,
            "tier1_section_catalog": section_keys,
            "tier1_section_catalog_detail": tier1_section_catalog_detail(),
            "default_tier1_sections_by_agent": DEFAULT_TIER1_SECTIONS_BY_AGENT,
        }

    @classmethod
    def validate_registry(cls, registry: Dict[str, Any]) -> Tuple[bool, str]:
        agents = (registry or {}).get("agents") or []
        if not agents:
            return False, "agents 不能为空"
        return True, ""

    @classmethod
    def save_registry(cls, registry: Dict[str, Any], *, note: str = "", activate: bool = True) -> None:
        raise ValueError("registry v2 已下线，请使用 /api/admin/agent/definitions/ 管理 drama.* 角色")

    @classmethod
    def ensure_defaults(cls) -> None:
        from apps.agent.definition_service import AgentDefinitionService

        AgentDefinitionService.ensure_defaults()
        cls.clear_cache()

    @classmethod
    def get_active_row(cls):
        return None

    @classmethod
    def import_from_file(cls, *, overwrite: bool = True) -> None:
        raise ValueError("registry v2 文件导入已下线，请使用 seed_drama_skills")

    @classmethod
    def migrate_pipeline_skill_config(cls) -> int:
        return 0
