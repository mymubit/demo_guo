# -*- coding: utf-8 -*-
"""Agent sub_skill LLM 调用（FusionPromptBuilder + LlmService）。"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..models import Project

logger = logging.getLogger(__name__)


def run_sub_skill_llm(
    project: Project,
    *,
    agent_id: str,
    fusion_node_id: str,
    sub_skill_id: str,
    upstream: Dict[str, Any],
    system_hint: str = "",
) -> Dict[str, Any]:
    """按 registry sub_skill 定义调用 LLM，返回解析后的 JSON dict。"""
    from apps.agent.routes import AgentLlmRouteService
    from apps.creation.monitoring.execution_run_service import get_active_run_id
    from apps.creation.orchestration.llm_tokens import resolve_agent_max_tokens
    from apps.creation.orchestration.sub_skill_runner import sub_skill_meta
    from apps.skill.llm.chat import LlmService, LlmServiceError
    from apps.skill.llm.usage_log import llm_usage_scope
    from apps.skill.models import LlmUsageLog
    from apps.skill.skills.skill_hint_resolver import resolve_system_hint
    from apps.workflow.fusion.prompt_builder import FusionPromptBuilder

    if not LlmService.is_enabled():
        raise LlmServiceError("LLM 未启用")

    meta = sub_skill_meta(agent_id, sub_skill_id) or {"id": sub_skill_id}
    hint = system_hint or resolve_system_hint(
        skill_id=sub_skill_id,
        fallback_hint="",
        user_id=project.user_id,
        project_id=str(project.id),
    )
    builder = FusionPromptBuilder()
    system_prompt, user_prompt = builder.build_sub_skill(
        fusion_node_id,
        sub_skill_id,
        meta,
        upstream,
        system_hint=hint,
    )
    route_key = agent_id if sub_skill_id in {"reference-injector", "rhythm-calibrator"} else agent_id
    provider_id = AgentLlmRouteService.resolve_provider_id(route_key)
    max_tokens = (
        AgentLlmRouteService.resolve_max_tokens(sub_skill_id)
        or AgentLlmRouteService.resolve_max_tokens(agent_id)
        or resolve_agent_max_tokens(agent_id)
    )
    source_key = f"{fusion_node_id}:{sub_skill_id}"[:64]
    with llm_usage_scope(
        source_type=LlmUsageLog.SOURCE_AGENT,
        source_key=source_key,
        project_id=str(project.id),
        user_id=project.user_id,
        execution_run_id=get_active_run_id(),
        sub_skill_id=sub_skill_id[:64],
    ):
        return LlmService.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            provider_id=provider_id,
            max_tokens=max_tokens,
            upstream=upstream,
            trace_extra={
                "agent_id": agent_id,
                "fusion_node_id": fusion_node_id,
                "sub_skill_id": sub_skill_id,
                "system_hint": hint[:2000] if hint else "",
            },
        )
