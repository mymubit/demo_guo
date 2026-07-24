# -*- coding: utf-8 -*-
"""外界剧本评审执行器：复用 scorer/compliance，不写 V3ArtifactVersion。"""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from django.conf import settings

from apps.drama.models import DramaLlmCallLog, ScriptReview, V3CommandRun
from apps.drama.services.artifact_normalize import normalize_artifact
from apps.drama.services.llm_call_context import llm_call_scope
from apps.drama.services.script_review_service import (
    stub_episode_plan,
    stub_project_brief,
    wrap_script_as_episode_scripts,
)
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.skills_bridge.executor import GenerationError, _map_payloads, _role_to_agent_id
from apps.drama.skills_bridge.recipe_map import recipe_for
from apps.drama.skills_bridge.validate import validate_artifact_payload

_SKILL_PROMPT_CHARS = 2000
_EXTERNAL_SYSTEM_COMMANDS = frozenset(
    {"score_external_script", "check_external_compliance"}
)


def _resolve_llm_call() -> Callable[..., str] | None:
    override = getattr(settings, "V3_LLM_CALL_OVERRIDE", None)
    if override is None or not callable(override):
        return None
    return override


def _normalize_settings(review: ScriptReview) -> dict[str, Any]:
    settings_map: dict[str, Any] = {
        "title": review.title,
        "entry_type": "original",
        "resolved_script_key": "external_script",
        "external_script_review": True,
    }
    if review.project_id and isinstance(review.project.settings, dict):
        raw = dict(review.project.settings)
        settings_map.update(raw)
        settings_map.setdefault("title", review.title)
        settings_map.setdefault("entry_type", review.project.entry_type)
        settings_map["resolved_script_key"] = "external_script"
        settings_map["external_script_review"] = True
    return settings_map


def _build_external_prompt(
    *,
    command_type: str,
    recipe: dict[str, Any],
    review: ScriptReview,
) -> str:
    loader = get_skills_loader()
    agent_id = _role_to_agent_id(str(recipe.get("role") or ""))
    skill_body = loader.load_skill(agent_id)[:_SKILL_PROMPT_CHARS]

    scripts = wrap_script_as_episode_scripts(
        title=review.title, script_text=review.script_text
    )
    deps = {
        "episode_scripts": scripts,
        "episode_plan": stub_episode_plan(title=review.title),
        "project_brief": stub_project_brief(title=review.title),
    }
    user_ctx: dict[str, Any] = {
        "project": {
            "title": review.title,
            "entry_type": (
                review.project.entry_type if review.project_id else "original"
            ),
            "stage": "quality",
            "settings": {"title": review.title},
        },
        "command_type": command_type,
        "recipe_id": recipe.get("recipe_id"),
        "writes": recipe.get("writes"),
        "committed_dependencies": deps,
        "request_payload": {
            "script_review_id": str(review.id),
            "source": "external_script_review",
        },
    }
    if command_type in _EXTERNAL_SYSTEM_COMMANDS:
        from apps.drama.orchestrator.system_config import resolve_system_config

        effective = resolve_system_config()["effective"]
        user_ctx["scoring_preset"] = effective.get("scoring_preset")
        user_ctx["target_platform"] = effective.get("target_platform")
        user_ctx["system_config"] = {
            "scoring_preset": effective.get("scoring_preset"),
            "target_platform": effective.get("target_platform"),
            "pass_threshold": effective.get("pass_threshold"),
            "platform_label_zh": effective.get("platform_label_zh"),
        }

    return (
        f"{skill_body}\n\n"
        f"## 用户输入\n"
        f"{json.dumps(user_ctx, ensure_ascii=False)}\n\n"
        f"请只输出合法 JSON（不要 Markdown 代码块）。"
    )


def _default_llm_call(prompt: str, *, role: str = "") -> str:
    from apps.drama.skills_bridge.executor import _default_llm_call as _inner

    return _inner(prompt, role=role)


def execute_external_script_review(
    *,
    command_type: str,
    review: ScriptReview,
    run: V3CommandRun,
    llm_call: Callable[..., str] | None = None,
) -> dict[str, Any]:
    """执行外界评分/合规；返回报告 payload，不创建 artifact。"""
    if command_type not in _EXTERNAL_SYSTEM_COMMANDS:
        raise GenerationError(f"不支持的外界评审命令: {command_type}")

    recipe = recipe_for(command_type)
    writes: list[str] = list(recipe["writes"])
    if len(writes) != 1:
        raise GenerationError("外界评审配方须且仅写一个报告产物")

    prompt = _build_external_prompt(
        command_type=command_type, recipe=recipe, review=review
    )
    role = str(recipe.get("role") or "")
    caller = llm_call if llm_call is not None else _resolve_llm_call()
    if caller is None:
        caller = lambda p, _role=role: _default_llm_call(p, role=_role)

    actor = getattr(run.owner, "username", None) or str(run.owner_id)
    from apps.drama.orchestrator.llm_router import failover_call_scope

    with failover_call_scope(owner=run.owner, run=run, project=review.project):
        with llm_call_scope(
            v3_command_run_id=str(run.id),
            v3_project_id=str(review.project_id) if review.project_id else None,
            role=_role_to_agent_id(role),
            purpose=DramaLlmCallLog.Purpose.ARTIFACT_GENERATION,
            actor=actor,
        ):
            raw_text = caller(prompt)

    payload_by_key = _map_payloads(writes=writes, raw_text=raw_text)
    artifact_key = writes[0]
    payload = payload_by_key[artifact_key]
    normalize_settings = _normalize_settings(review)
    try:
        normalized = normalize_artifact(artifact_key, payload, normalize_settings)
    except ValueError as exc:
        raise GenerationError(f"产物 {artifact_key} 归一化失败: {exc}") from exc
    if not isinstance(normalized, dict):
        raise GenerationError(f"产物 {artifact_key} 归一化后必须是 JSON 对象")
    errors = validate_artifact_payload(artifact_key, normalized)
    if errors:
        raise GenerationError(f"产物 {artifact_key} 校验失败: {errors[0]}")
    return normalized
