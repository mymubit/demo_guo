# -*- coding: utf-8 -*-
"""Agent LLM 路由 — 运行时只读 AgentLlmRouteConfig（DB）。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from apps.agent.bootstrap.agent_llm_routes import ROUTE_SEED

logger = logging.getLogger(__name__)
class AgentLlmRouteService:
    @staticmethod
    def resolve_provider_id(route_key: str) -> Optional[str]:
        """Agent LLM Provider — 主链与辅助 Agent 统一走 AgentLlmRouteConfig。"""
        key = (route_key or "").strip().lower()
        if not key:
            return None
        from apps.agent.models import AgentLlmRouteConfig
        from apps.skill.models import LlmProvider

        row = (
            AgentLlmRouteConfig.objects.filter(route_key=key, is_active=True)
            .select_related("llm_provider")
            .first()
        )
        if row and row.llm_provider_id and row.llm_provider and row.llm_provider.is_enabled:
            return str(row.llm_provider_id)
        active = LlmProvider.objects.filter(is_active=True, is_enabled=True).first()
        return str(active.id) if active else None

    @staticmethod
    def resolve_max_tokens(route_key: str) -> Optional[int]:
        key = (route_key or "").strip()
        if not key:
            return None

        from apps.agent.models import AgentLlmRouteConfig

        row = AgentLlmRouteConfig.objects.filter(route_key=key, is_active=True).first()
        if row and row.max_tokens:
            return max(256, int(row.max_tokens))

        return None

    @staticmethod
    def resolve_node_max_tokens(node_id: str) -> Optional[int]:
        from apps.agent.binding import agent_id_for_fusion_node

        agent_id = agent_id_for_fusion_node(node_id)
        if agent_id:
            tokens = AgentLlmRouteService.resolve_max_tokens(agent_id)
            if tokens:
                return tokens
        return None

    @staticmethod
    def resolve_provider_id_for_node(fusion_node_id: str) -> Optional[str]:
        from apps.agent.binding import agent_id_for_fusion_node

        agent_id = agent_id_for_fusion_node(fusion_node_id)
        if agent_id:
            provider_id = AgentLlmRouteService.resolve_provider_id(agent_id)
            if provider_id:
                return provider_id
        from apps.workflow.step_admin import PipelineStepAdminService

        return PipelineStepAdminService._legacy_resolve_provider_id(fusion_node_id)

    @classmethod
    def seed_defaults(cls) -> int:
        from apps.agent.models import AgentLlmRouteConfig

        created = 0
        for item in ROUTE_SEED:
            _, was_created = AgentLlmRouteConfig.objects.get_or_create(
                route_key=item["route_key"],
                defaults={
                    "display_name": item.get("display_name") or item["route_key"],
                    "max_tokens": item.get("max_tokens"),
                    "sort_order": int(item.get("sort_order") or 0),
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
        return created

    @staticmethod
    def list_admin_items() -> List[Dict[str, Any]]:
        from apps.agent.models import AgentLlmRouteConfig

        rows = AgentLlmRouteConfig.objects.select_related("llm_provider").order_by(
            "sort_order", "route_key"
        )
        items = []
        for row in rows:
            provider = row.llm_provider
            items.append(
                {
                    "id": str(row.id),
                    "route_key": row.route_key,
                    "display_name": row.display_name,
                    "max_tokens": row.max_tokens,
                    "is_active": row.is_active,
                    "sort_order": row.sort_order,
                    "llm_provider_id": str(row.llm_provider_id) if row.llm_provider_id else None,
                    "llm_provider_name": provider.name if provider else None,
                    "updated_at": row.updated_at,
                }
            )
        return items

    @staticmethod
    def upsert(route_key: str, data: Dict[str, Any]):
        from apps.agent.models import AgentLlmRouteConfig
        from apps.skill.models import LlmProvider

        key = (route_key or "").strip()
        if not key:
            raise ValueError("route_key 不能为空")

        row, _ = AgentLlmRouteConfig.objects.get_or_create(
            route_key=key,
            defaults={
                "display_name": str(data.get("display_name") or key)[:128],
                "sort_order": int(data.get("sort_order") or 0),
            },
        )
        if "display_name" in data:
            row.display_name = str(data["display_name"] or row.display_name)[:128]
        if "max_tokens" in data:
            val = data["max_tokens"]
            row.max_tokens = max(256, int(val)) if val not in (None, "") else None
        if "is_active" in data:
            row.is_active = bool(data["is_active"])
        if "sort_order" in data:
            row.sort_order = int(data["sort_order"] or 0)
        if "llm_provider_id" in data:
            raw = data.get("llm_provider_id")
            if not raw:
                row.llm_provider = None
            else:
                row.llm_provider = LlmProvider.objects.filter(pk=raw, is_enabled=True).first()
        row.save()
        return row
