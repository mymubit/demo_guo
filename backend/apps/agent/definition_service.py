"""独立 Agent 定义、种子数据与健康检查 — drama.* 新体系。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.db import transaction

from apps.agent.independent_defaults import (
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_USER_PROMPT_TEMPLATE,
    get_drama_agent_defaults,
)
from apps.agent.models import (
    AgentDefinition,
    AgentKnowledgeBinding,
    AgentPromptVersion,
    AgentLlmRouteConfig,
)


class AgentDefinitionService:
    @staticmethod
    def ensure_defaults() -> int:
        """
        种入 drama.* 36个角色到 AgentDefinition。
        推荐使用：python manage.py seed_drama_skills
        """
        drama_defaults = get_drama_agent_defaults()
        created = 0
        with transaction.atomic():
            for index, item in enumerate(drama_defaults, start=1):
                enabled = bool(item.get("enabled", True))
                agent, was_created = AgentDefinition.objects.update_or_create(
                    agent_id=item["agent_id"],
                    defaults={
                        "name": item["name"],
                        "name_zh": item["name_zh"],
                        "description": item["description"],
                        "category": "drama_skills",
                        "workspace_order": item.get("workspace_order") or index,
                        "is_enabled": enabled,
                        "is_system": True,
                        "version": "v1",
                        "lifecycle_status": (
                            AgentDefinition.LifecycleStatus.ACTIVE
                            if enabled
                            else AgentDefinition.LifecycleStatus.DISABLED
                        ),
                        "default_output_artifact_key": item["default_output_artifact_key"],
                        "input_contract": item.get("input_contract") or {},
                        "output_contract": item.get("output_contract") or {},
                        "runtime_policy": item.get("runtime_policy") or {},
                        "ui_schema": item.get("ui_schema") or {},
                    },
                )
                if was_created:
                    created += 1
                AgentPromptVersion.objects.get_or_create(
                    agent=agent,
                    version="v1",
                    defaults={
                        "system_prompt": DEFAULT_SYSTEM_PROMPT,
                        "user_prompt_template": DEFAULT_USER_PROMPT_TEMPLATE,
                        "output_format_prompt": "输出必须是 JSON 对象；顶层可用 artifact_key 与 payload，artifact_key 只能取契约声明的产物键，禁止自创。",
                        "constraints_prompt": "不得触发其他 Agent；不得引用外部目录；不得输出非 JSON 文本。",
                        "few_shot_examples": [],
                        "is_active": True,
                        "change_notes": "独立 Agent 默认 Prompt",
                        "created_by": "system",
                    },
                )
                route, _ = AgentLlmRouteConfig.objects.get_or_create(
                    route_key=item["agent_id"],
                    defaults={
                        "agent": agent,
                        "display_name": item["name_zh"],
                        "max_tokens": item.get("runtime_policy", {}).get("max_completion_tokens"),
                        "max_prompt_tokens": item.get("runtime_policy", {}).get("max_prompt_tokens"),
                        "max_completion_tokens": item.get("runtime_policy", {}).get("max_completion_tokens"),
                        "timeout_seconds": item.get("runtime_policy", {}).get("timeout_seconds") or 600,
                        "temperature": 0.7,
                        "is_active": True,
                        "sort_order": item.get("workspace_order") or index,
                    },
                )
                if route.agent_id is None:
                    route.agent = agent
                    route.save(update_fields=["agent"])
            AgentDefinitionService.ensure_route_providers()
        return created

    @staticmethod
    def ensure_route_providers() -> int:
        """为未绑定 Provider 的 Agent 路由自动挂上当前全局启用的 Provider。"""
        from apps.skill.models import LlmProvider

        provider = LlmProvider.objects.filter(is_active=True, is_enabled=True).first()
        if not provider:
            return 0
        updated = 0
        routes = AgentLlmRouteConfig.objects.filter(is_active=True, llm_provider__isnull=True)
        for route in routes:
            route.llm_provider = provider
            route.save(update_fields=["llm_provider", "updated_at"])
            updated += 1
        return updated

    @staticmethod
    def active_agents() -> List[AgentDefinition]:
        return list(
            AgentDefinition.objects.filter(
                lifecycle_status=AgentDefinition.LifecycleStatus.ACTIVE,
                is_enabled=True,
            ).order_by("workspace_order", "agent_id")
        )

    @staticmethod
    def get_runnable(agent_id: str) -> AgentDefinition:
        agent = AgentDefinition.objects.filter(agent_id=agent_id).first()
        if agent is None:
            raise ValueError(f"Agent 不存在: {agent_id}")
        if not agent.is_enabled or agent.lifecycle_status != AgentDefinition.LifecycleStatus.ACTIVE:
            raise ValueError(f"Agent 已停用: {agent_id}")
        return agent

    @staticmethod
    def active_prompt(agent: AgentDefinition) -> AgentPromptVersion:
        prompt = agent.prompt_versions.filter(is_active=True).order_by("-created_at").first()
        if prompt is None:
            raise ValueError(f"Agent 缺少 active prompt: {agent.agent_id}")
        return prompt

    @staticmethod
    def active_route(agent: AgentDefinition) -> AgentLlmRouteConfig:
        route = (
            AgentLlmRouteConfig.objects.filter(agent=agent, is_active=True)
            .select_related("llm_provider")
            .first()
        )
        if route is None:
            route = (
                AgentLlmRouteConfig.objects.filter(route_key=agent.agent_id, is_active=True)
                .select_related("llm_provider")
                .first()
            )
        if route is None or not route.llm_provider_id:
            raise ValueError(f"Agent 缺少明确模型路由: {agent.agent_id}")
        if route.llm_provider and not route.llm_provider.is_enabled:
            raise ValueError(f"Agent 模型 Provider 已停用: {agent.agent_id}")
        return route

    @staticmethod
    def enabled_bindings(agent: AgentDefinition) -> List[AgentKnowledgeBinding]:
        return list(
            agent.knowledge_bindings.filter(is_enabled=True, knowledge__is_enabled=True)
            .select_related("knowledge")
            .order_by("order_index", "knowledge__priority")
        )

    @staticmethod
    def health(agent: AgentDefinition) -> Dict[str, Any]:
        prompt_ok = agent.prompt_versions.filter(is_active=True).exists()
        route = (
            AgentLlmRouteConfig.objects.filter(agent=agent, is_active=True)
            .select_related("llm_provider")
            .first()
            or AgentLlmRouteConfig.objects.filter(route_key=agent.agent_id, is_active=True)
            .select_related("llm_provider")
            .first()
        )
        route_ok = bool(route and route.llm_provider_id)
        contract_ok = bool(agent.input_contract and agent.output_contract)
        return {
            "agent_id": agent.agent_id,
            "prompt_ok": prompt_ok,
            "route_ok": route_ok,
            "contract_ok": contract_ok,
            "healthy": prompt_ok and route_ok and contract_ok,
            "route_key": route.route_key if route else "",
            "provider_name": route.llm_provider.name if route and route.llm_provider else "",
        }

    @staticmethod
    def admin_list() -> List[Dict[str, Any]]:
        agents = AgentDefinition.objects.filter(
            agent_id__startswith="drama.",
        ).order_by("workspace_order", "agent_id")
        return [
            {
                "id": str(agent.id),
                "agent_id": agent.agent_id,
                "name": agent.name,
                "name_zh": agent.name_zh,
                "description": agent.description,
                "category": agent.category,
                "workspace_order": agent.workspace_order,
                "is_enabled": agent.is_enabled,
                "lifecycle_status": agent.lifecycle_status,
                "default_output_artifact_key": agent.default_output_artifact_key,
                "input_contract": agent.input_contract or {},
                "output_contract": agent.output_contract or {},
                "runtime_policy": agent.runtime_policy or {},
                "ui_schema": agent.ui_schema or {},
                "health": AgentDefinitionService.health(agent),
            }
            for agent in agents
        ]
