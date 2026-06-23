# -*- coding: utf-8 -*-
# apps/agent/services.py
# Agent 服务门面层 — drama.* 体系
from __future__ import annotations

from typing import Any, Dict, List, Optional

from apps.agent.registry import AgentRegistryConfigService
from apps.agent.routes import AgentLlmRouteService


class AgentService:
    @staticmethod
    def get_registry_payload() -> Dict[str, Any]:
        return AgentRegistryConfigService.admin_payload()

    @staticmethod
    def save_registry(registry: Dict[str, Any], *, note: str = "") -> None:
        AgentRegistryConfigService.save_registry(registry, note=note)

    @staticmethod
    def import_registry_from_file(*, overwrite: bool = True) -> None:
        AgentRegistryConfigService.import_from_file(overwrite=overwrite)

    @staticmethod
    def ensure_registry_defaults() -> None:
        AgentRegistryConfigService.ensure_defaults()

    @staticmethod
    def migrate_pipeline_skill_config() -> int:
        return AgentRegistryConfigService.migrate_pipeline_skill_config()

    @staticmethod
    def resolve_llm_provider_id(route_key: str) -> Optional[str]:
        return AgentLlmRouteService.resolve_provider_id(route_key)

    @staticmethod
    def resolve_llm_provider_for_agent(agent_id: str) -> Optional[str]:
        return AgentLlmRouteService.resolve_provider_id(agent_id)

    @staticmethod
    def resolve_max_tokens(route_key: str) -> Optional[int]:
        return AgentLlmRouteService.resolve_max_tokens(route_key)

    @staticmethod
    def list_llm_routes() -> List[Dict[str, Any]]:
        return AgentLlmRouteService.list_admin_items()

    @staticmethod
    def upsert_llm_route(route_key: str, data: Dict[str, Any]) -> None:
        AgentLlmRouteService.upsert(route_key, data)

    @staticmethod
    def seed_llm_route_defaults() -> int:
        return AgentLlmRouteService.seed_defaults()

    @staticmethod
    def portal_catalog() -> Dict[str, Any]:
        from apps.agent.catalog import portal_agent_catalog

        return portal_agent_catalog()

    @staticmethod
    def clear_runtime_cache() -> None:
        AgentRegistryConfigService.clear_cache()
