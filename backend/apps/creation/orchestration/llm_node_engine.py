# -*- coding: utf-8 -*-
"""通用 LLM 节点执行（World / Character 等单轮 JSON 生成）。"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from apps.agent.routes import AgentLlmRouteService
from apps.workflow.fusion.schema_validator import validate_against_schema
from apps.skill.llm.chat import LlmService, LlmServiceError

from ..pipeline_debug_log import log_fusion_node_begin, summarize_artifact
from .llm_tokens import resolve_agent_max_tokens
from .sub_skill_runner import inject_knowledge_upstream

if TYPE_CHECKING:
    from ..fusion.fusion_orchestrator import FusionOrchestrator

logger = logging.getLogger(__name__)


def run_llm_node(
    orch: FusionOrchestrator,
    *,
    agent_id: str,
    node_id: str,
    upstream: Dict[str, Any],
    post_process: Optional[Callable[[dict], dict]] = None,
) -> dict:
    """执行单轮 LLM 节点并做 schema 校验。"""
    if not LlmService.is_enabled():
        raise LlmServiceError(
            f"{node_id} 需要 LLM：请设置 FUSION_LLM_ENABLED=true 并配置 llm.enabled / api_key / base_url"
        )

    orch._mark_node_running(node_id)
    from apps.workflow.fusion.registry import FusionNodeRegistry

    node = FusionNodeRegistry(orch.config).node_by_fusion_id(node_id) or {}
    schema_file = (node.get("schemaFile") or "").replace("schemas/", "")

    prompt_upstream = inject_knowledge_upstream(agent_id, dict(upstream), orch.project)
    system, user = orch.prompts.build(node_id, prompt_upstream)

    provider_id = AgentLlmRouteService.resolve_provider_id(agent_id)
    log_fusion_node_begin(
        project_id=orch.project.id,
        node_id=node_id,
        node_index=orch._node_index(node_id),
        upstream={"agentId": agent_id, **upstream},
        prompt_stats={
            "providerId": provider_id,
            "systemPromptLen": len(system or ""),
            "userPromptLen": len(user or ""),
        },
    )
    max_tokens = resolve_agent_max_tokens(agent_id)
    from apps.skill.llm.usage_log import llm_usage_scope
    from apps.skill.models import LlmUsageLog

    with llm_usage_scope(
        source_type=LlmUsageLog.SOURCE_NODE,
        source_key=node_id,
        project_id=orch.project.id,
        user_id=orch.project.user_id,
        sub_skill_id=agent_id,
    ):
        payload = LlmService.generate_json(
            system_prompt=system,
            user_prompt=user,
            provider_id=provider_id,
            max_tokens=max_tokens,
        )

    if post_process:
        payload = post_process(payload)

    ok, msgs = validate_against_schema(payload, f"schemas/{schema_file}", config=orch.config)
    if not ok:
        logger.warning(
            "Agent %s node %s schema 警告: %s output=%s",
            agent_id,
            node_id,
            msgs[:5],
            summarize_artifact(
                orch.artifact_registry.primary_artifact_for_fusion_node(node_id) or node_id,
                payload,
            ),
        )
        if orch.strict_schema:
            raise ValueError(f"{node_id} schema 校验失败: {'; '.join(msgs[:5])}")

    return payload
