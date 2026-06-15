# -*- coding: utf-8 -*-
"""PolishAgent：文本/创意润色建议（默认 suggest，可配置自动 apply）。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from django.conf import settings

from ..artifact_service import get_artifact, save_artifact
from ..models import Project
from .sub_skill_runner import (
    agent_execution_meta,
    mark_executed,
    persist_agent_execution_trace,
)
from .types import AgentResult

logger = logging.getLogger(__name__)


def _build_polish_suggestions(review_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues = review_report.get("issues") or []
    pacing = review_report.get("pacing") or {}
    suggestions: List[Dict[str, Any]] = []
    for item in issues[:8]:
        suggestions.append({"type": "review_issue", "text": str(item), "action": "polish-text"})
    for item in (pacing.get("assessments") or [])[:5]:
        if "不足" in item or "过于" in item or "波动" in item:
            suggestions.append({"type": "pacing", "text": str(item), "action": "polish-creative"})
    return suggestions


def _try_llm_polish(project: Project, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not suggestions:
        return []
    try:
        from apps.skill.llm.chat import LlmService, LlmServiceError

        if not LlmService.is_enabled():
            return suggestions
    except Exception:  # noqa: BLE001
        return suggestions

    scripts = get_artifact(project, "episode_scripts") or {}
    sample_eps = (scripts.get("episodes") or [])[:2]
    _base_system = (
        "你是短剧润色顾问。根据质检与节奏问题，给出可执行的修改建议（不直接输出整集剧本）。"
        "输出 JSON：{\"suggestions\":[{\"episodeNumber\":1,\"field\":\"dialogue\",\"advice\":\"...\"}]}"
    )
    # 注入 Tier1 润色相关规则（写作禁令 + 台词质量 + AI腔禁用）
    try:
        from apps.skill.skills.loader import get_skill_rule_loader
        loader = get_skill_rule_loader()
        rule_snippet = loader.build_tier1_node_snippet("node-7-polish")
        system = (_base_system + "\n\n" + rule_snippet) if rule_snippet else _base_system
    except Exception:
        system = _base_system
    user = {
        "issues": suggestions,
        "sampleEpisodes": sample_eps,
        "projectTitle": project.title,
    }
    try:
        from apps.skill.llm.chat import LlmService

        import json

        from apps.creation.orchestration.llm_tokens import resolve_agent_max_tokens
        from apps.agent.routes import AgentLlmRouteService

        from apps.creation.monitoring.execution_run_service import get_active_run_id
        from apps.skill.llm.usage_log import llm_usage_scope
        from apps.skill.models import LlmUsageLog

        with llm_usage_scope(
            source_type=LlmUsageLog.SOURCE_AGENT,
            source_key="polish:polish-text"[:64],
            project_id=project.id,
            user_id=project.user_id,
            execution_run_id=get_active_run_id(),
            sub_skill_id="polish-text",
        ):
            raw = LlmService.generate_json(
                system_prompt=system,
                user_prompt=json.dumps(user, ensure_ascii=False),
                provider_id=AgentLlmRouteService.resolve_provider_id("polish"),
                max_tokens=resolve_agent_max_tokens("polish"),
            )
        llm_items = raw.get("suggestions") if isinstance(raw, dict) else []
        if isinstance(llm_items, list) and llm_items:
            return llm_items
    except Exception as exc:  # noqa: BLE001
        logger.warning("[PolishAgent] LLM polish skipped: %s", exc)
    return suggestions


def run_polish_agent(
    project: Project,
    *,
    mode: str = "suggest",
    review_report: Dict[str, Any] | None = None,
) -> AgentResult:
    review_report = review_report or get_artifact(project, "review_report") or {}
    executed: list = []
    if review_report.get("passed"):
        trace_meta = agent_execution_meta("polish", executed, node_index=0)
        persist_agent_execution_trace(project, "polish", executed)
        return AgentResult(
            agent_id="polish",
            status="skipped",
            meta={**trace_meta, "reason": "review_passed"},
        )

    mark_executed(executed, "polish-diff-builder")
    base_suggestions = _build_polish_suggestions(review_report)
    suggestions = _try_llm_polish(project, base_suggestions)
    mark_executed(executed, "polish-text")
    if any(
        isinstance(s, dict)
        and (s.get("type") == "pacing" or s.get("action") == "polish-creative")
        for s in base_suggestions
    ):
        mark_executed(executed, "polish-creative")
    polish_log: Dict[str, Any] = {
        "agentId": "polish",
        "mode": mode,
        "suggestions": suggestions,
        "applied": False,
    }

    auto_apply = bool(getattr(settings, "AGENT_POLISH_AUTO_APPLY", False))
    if mode == "apply" or auto_apply:
        from .polish_apply import apply_polish_suggestions

        try:
            apply_out = apply_polish_suggestions(
                project,
                apply_all=True,
                patch_script_fields=bool(getattr(settings, "AGENT_POLISH_PATCH_SCRIPT", False)),
            )
            polish_log = apply_out.get("polish_log") or polish_log
            mark_executed(executed, "polish-apply")
        except Exception as exc:  # noqa: BLE001
            logger.warning("[PolishAgent] auto apply skipped: %s", exc)
            polish_log["applyError"] = str(exc)[:300]

    save_artifact(project, "polish_log", polish_log)
    trace_meta = agent_execution_meta("polish", executed, node_index=0)
    persist_agent_execution_trace(project, "polish", executed)
    return AgentResult(
        agent_id="polish",
        status="completed",
        outputs={"polish_log": polish_log},
        meta={**trace_meta, "suggestion_count": len(suggestions)},
    )
