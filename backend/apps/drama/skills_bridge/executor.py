# -*- coding: utf-8 -*-
"""V3 skills_bridge：可注入 mock 的 LLM 生成执行器。"""
from __future__ import annotations

import copy
import json
from collections.abc import Callable
from typing import Any

from django.db import transaction

from apps.drama.models import DramaLlmCallLog, V3ArtifactVersion, V3CommandRun, V3Project
from apps.drama.orchestrator.artifacts import latest, next_version
from apps.drama.orchestrator.report_meta import attach_script_meta, strip_meta_for_validate
from apps.drama.services.artifact_normalize import normalize_artifact
from apps.drama.services.llm_call_context import llm_call_scope
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.skills_bridge.recipe_map import recipe_for
from apps.drama.skills_bridge.validate import validate_artifact_payload

_SKILL_PROMPT_CHARS = 2000
_PROVIDER_HINT = "请先在模型配置中配置并启用供应商"
_COMMIT_MODE_DIRECT = "direct"
_COMMIT_MODE_CANDIDATE = "candidate"
_SYSTEM_CONFIG_COMMANDS = frozenset(
    {"score_quality", "check_compliance", "prepare_delivery"}
)


class GenerationError(Exception):
    """生成失败（校验 / JSON / Provider 等）。"""


def merge_episode_plan_revision(
    *,
    committed_payload: dict[str, Any],
    llm_payload: dict[str, Any],
    episode_numbers: list[int] | None = None,
) -> dict[str, Any]:
    """
    将 LLM 返回的局部 episodes 合并进 committed plan 拷贝。

    - 仅替换 episode_numbers 范围内（或 LLM 返回）的卡片
    - 范围外卡片保持原样
    """
    if not isinstance(committed_payload, dict):
        raise GenerationError("已确认分集计划格式无效")
    if not isinstance(llm_payload, dict):
        raise GenerationError("修订返回必须是 JSON 对象")

    merged = copy.deepcopy(committed_payload)
    base_episodes = merged.get("episodes")
    if not isinstance(base_episodes, list) or not base_episodes:
        raise GenerationError("已确认分集计划缺少 episodes")

    llm_episodes = llm_payload.get("episodes")
    if not isinstance(llm_episodes, list) or not llm_episodes:
        raise GenerationError("修订返回缺少 episodes")

    allowed: set[int] | None = None
    if episode_numbers:
        allowed = {int(n) for n in episode_numbers}

    replacements: dict[int, dict[str, Any]] = {}
    for card in llm_episodes:
        if not isinstance(card, dict) or "episode" not in card:
            raise GenerationError("修订 episodes 项缺少 episode 字段")
        try:
            num = int(card["episode"])
        except (TypeError, ValueError) as exc:
            raise GenerationError("修订 episode 编号无效") from exc
        if allowed is not None and num not in allowed:
            continue
        replacements[num] = card

    if not replacements:
        raise GenerationError("修订未包含可合并的分集卡片")

    new_episodes: list[dict[str, Any]] = []
    for card in base_episodes:
        if not isinstance(card, dict) or "episode" not in card:
            raise GenerationError("已确认分集计划卡片格式无效")
        try:
            num = int(card["episode"])
        except (TypeError, ValueError) as exc:
            raise GenerationError("已确认分集计划 episode 编号无效") from exc
        if num in replacements:
            new_episodes.append(copy.deepcopy(replacements[num]))
        else:
            new_episodes.append(copy.deepcopy(card))

    merged["episodes"] = new_episodes
    return merged


def execute_generation(
    *,
    command_type: str,
    project: V3Project,
    run: V3CommandRun,
    llm_call: Callable[..., str] | None = None,
) -> list[V3ArtifactVersion]:
    """
    1) recipe_for(command_type)
    2) 组装最小 prompt（角色 SKILL 前缀 + 项目上下文 + committed 依赖）
    3) llm_call(prompt) -> JSON text；默认走 LlmProvider
    4) 解析 JSON；按 writes 拆分或整包映射
    5) revise_episode_plan：合并局部 episodes 到 committed 拷贝
    6) normalize（注入 theme_code/matrix_key 等合成字段）→ validate；失败 raise GenerationError
    7) 按 commit_mode 落库：
       - candidate（默认）：创建 candidate，supersede 旧 candidate
       - direct：attach_script_meta 后创建 committed，supersede 同 key 旧 committed+candidate
    """
    recipe = recipe_for(command_type)
    writes: list[str] = list(recipe["writes"])
    commit_mode = _resolve_commit_mode(recipe)
    _ensure_committed_dependencies(recipe=recipe, project=project)
    request_payload = run.request_payload if isinstance(run.request_payload, dict) else {}
    normalize_settings = _settings_for_normalize(project)
    prompt = _build_prompt(
        command_type=command_type,
        recipe=recipe,
        project=project,
        request_payload=request_payload,
    )
    role = str(recipe.get("role") or "")
    if llm_call is not None:
        caller = llm_call
    else:
        caller = lambda p, _role=role: _default_llm_call(p, role=_role)
    actor = getattr(run.owner, "username", None) or str(run.owner_id)
    from apps.drama.orchestrator.llm_router import failover_call_scope

    with failover_call_scope(owner=run.owner, run=run, project=project):
        with llm_call_scope(
            v3_command_run_id=str(run.id),
            v3_project_id=str(project.id),
            role=_role_to_agent_id(role),
            purpose=DramaLlmCallLog.Purpose.ARTIFACT_GENERATION,
            actor=actor,
        ):
            raw_text = caller(prompt)
    payload_by_key = _map_payloads(writes=writes, raw_text=raw_text)

    if command_type == "revise_episode_plan":
        payload_by_key["episode_plan"] = _apply_episode_plan_revision(
            project=project,
            llm_payload=payload_by_key["episode_plan"],
            request_payload=request_payload,
        )

    for artifact_key, payload in list(payload_by_key.items()):
        try:
            normalized = normalize_artifact(artifact_key, payload, normalize_settings)
        except ValueError as exc:
            raise GenerationError(
                f"产物 {artifact_key} 归一化失败: {exc}"
            ) from exc
        if not isinstance(normalized, dict):
            raise GenerationError(f"产物 {artifact_key} 归一化后必须是 JSON 对象")
        to_validate = (
            strip_meta_for_validate(normalized)
            if commit_mode == _COMMIT_MODE_DIRECT
            else normalized
        )
        errors = validate_artifact_payload(artifact_key, to_validate)
        if errors:
            raise GenerationError(
                f"产物 {artifact_key} 校验失败: {errors[0]}"
            )
        payload_by_key[artifact_key] = to_validate

    if commit_mode == _COMMIT_MODE_DIRECT:
        script_art = latest(
            project, "episode_scripts", status=V3ArtifactVersion.Status.COMMITTED
        )
        if script_art is None:
            raise GenerationError("请先确认正文后再继续")
        for artifact_key, payload in list(payload_by_key.items()):
            payload_by_key[artifact_key] = attach_script_meta(
                payload, script_art=script_art
            )

    created: list[V3ArtifactVersion] = []
    with transaction.atomic():
        target_status = (
            V3ArtifactVersion.Status.COMMITTED
            if commit_mode == _COMMIT_MODE_DIRECT
            else V3ArtifactVersion.Status.CANDIDATE
        )
        for artifact_key in writes:
            artifact = V3ArtifactVersion.objects.create(
                project=project,
                artifact_key=artifact_key,
                version=next_version(project.id, artifact_key),
                status=target_status,
                payload=payload_by_key[artifact_key],
                command_run=run,
            )
            created.append(artifact)
        created_ids = [item.id for item in created]
        for artifact_key in writes:
            if commit_mode == _COMMIT_MODE_DIRECT:
                # direct：同 key 旧 committed + candidate 一并 superseded
                V3ArtifactVersion.objects.filter(
                    project=project,
                    artifact_key=artifact_key,
                    status__in=(
                        V3ArtifactVersion.Status.COMMITTED,
                        V3ArtifactVersion.Status.CANDIDATE,
                    ),
                ).exclude(id__in=created_ids).update(
                    status=V3ArtifactVersion.Status.SUPERSEDED
                )
            else:
                # candidate：仅 supersede 同 key 旧 candidate
                V3ArtifactVersion.objects.filter(
                    project=project,
                    artifact_key=artifact_key,
                    status=V3ArtifactVersion.Status.CANDIDATE,
                ).exclude(id__in=created_ids).update(
                    status=V3ArtifactVersion.Status.SUPERSEDED
                )
    return created


def _resolve_commit_mode(recipe: dict[str, Any]) -> str:
    mode = recipe.get("commit_mode", _COMMIT_MODE_CANDIDATE)
    if mode == _COMMIT_MODE_DIRECT:
        return _COMMIT_MODE_DIRECT
    return _COMMIT_MODE_CANDIDATE


def _settings_for_normalize(project: V3Project) -> dict[str, Any]:
    """从项目 settings + template_seed 组装 normalize 用上下文。"""
    raw = project.settings if isinstance(project.settings, dict) else {}
    settings: dict[str, Any] = dict(raw)
    settings.setdefault("title", project.title)
    settings.setdefault("entry_type", project.entry_type)

    seed = settings.get("template_seed")
    if not isinstance(seed, dict):
        return settings

    theme = str(seed.get("theme_code") or "").strip()
    if theme and not str(settings.get("preset_theme_code") or "").strip():
        settings["preset_theme_code"] = theme

    dims = seed.get("dims")
    if isinstance(dims, dict):
        if not isinstance(settings.get("genre_matrix"), dict):
            genre_matrix = {
                key: dims[key]
                for key in ("emotion", "identity", "conflict", "world")
                if dims.get(key)
            }
            if genre_matrix:
                settings["genre_matrix"] = genre_matrix
        for key in (
            "audience_channel",
            "protagonist_structure",
            "flavor_tags",
        ):
            if key not in settings and dims.get(key) is not None:
                settings[key] = dims[key]
    return settings


def _role_to_agent_id(role: str) -> str:
    """recipe role（目录名）→ registry agent_id。"""
    if role.startswith("drama-"):
        return "drama." + role[len("drama-") :]
    return role


_DEPENDENCY_HINTS: dict[str, str] = {
    "project_brief": "请先确认选题简报后再生成蓝图",
    "story_bible": "请先确认故事蓝图后再生成分集计划",
    "episode_plan": "请先确认分集计划后再继续",
}


def _required_committed_keys(recipe: dict[str, Any]) -> list[str]:
    raw = recipe.get("requires_committed")
    if not isinstance(raw, list):
        return []
    return [key for key in raw if isinstance(key, str)]


def _ensure_committed_dependencies(*, recipe: dict[str, Any], project: V3Project) -> None:
    for key in _required_committed_keys(recipe):
        art = latest(project, key, status=V3ArtifactVersion.Status.COMMITTED)
        if art is None:
            raise GenerationError(_DEPENDENCY_HINTS.get(key, f"缺少已确认产物：{key}"))


def _parse_episode_numbers(request_payload: dict[str, Any]) -> list[int] | None:
    raw = request_payload.get("episode_numbers")
    if not isinstance(raw, list) or not raw:
        return None
    numbers: list[int] = []
    for item in raw:
        try:
            numbers.append(int(item))
        except (TypeError, ValueError) as exc:
            raise GenerationError("episode_numbers 必须为整数列表") from exc
    return numbers


def _apply_episode_plan_revision(
    *,
    project: V3Project,
    llm_payload: dict[str, Any],
    request_payload: dict[str, Any],
) -> dict[str, Any]:
    committed = latest(project, "episode_plan", status=V3ArtifactVersion.Status.COMMITTED)
    if committed is None:
        raise GenerationError(_DEPENDENCY_HINTS["episode_plan"])
    return merge_episode_plan_revision(
        committed_payload=committed.payload,
        llm_payload=llm_payload,
        episode_numbers=_parse_episode_numbers(request_payload),
    )


def _build_prompt(
    *,
    command_type: str,
    recipe: dict[str, Any],
    project: V3Project,
    request_payload: dict[str, Any] | None = None,
) -> str:
    loader = get_skills_loader()
    agent_id = _role_to_agent_id(str(recipe.get("role") or ""))
    skill_body = loader.load_skill(agent_id)[:_SKILL_PROMPT_CHARS]

    deps: dict[str, Any] = {}
    for key in _required_committed_keys(recipe):
        art = latest(project, key, status=V3ArtifactVersion.Status.COMMITTED)
        if art is not None:
            deps[key] = art.payload

    user_ctx: dict[str, Any] = {
        "project": {
            "title": project.title,
            "entry_type": project.entry_type,
            "stage": project.stage,
            "settings": _prompt_project_settings(project),
        },
        "command_type": command_type,
        "recipe_id": recipe.get("recipe_id"),
        "writes": recipe.get("writes"),
        "committed_dependencies": deps,
        "request_payload": request_payload or {},
    }
    if command_type in _SYSTEM_CONFIG_COMMANDS:
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

    contract_hint = ""
    if command_type == "generate_topic_brief":
        contract_hint = (
            "\n## 输出契约（project_brief）\n"
            "必须输出 JSON 对象，且至少包含：title、genre_matrix、episode_count、"
            "core_idea、target_audience、core_conflict、hook_concept、compliance_risk。\n"
            "genre_matrix 必填四轴，且必须使用英文枚举值（禁止中文标签）：\n"
            "- emotion: revenge|love|healing|suspense|ambition|comedy|justice|warmth|nostalgia\n"
            "- identity: underdog|reborn|hidden-elite|ordinary|outcast|student|protector|bound|returning-elite\n"
            "- conflict: family|workplace|romance|power|survival|crime|…\n"
            "- world: modern|ancient|fantasy|…；audience_channel: female|male|general\n"
            "若 project.settings.template_seed.dims 已有四轴，优先沿用并补全卖点字段；"
            "theme_code / matrix_key / rule_params 可由系统补全。\n"
        )
    elif command_type == "generate_blueprint":
        contract_hint = (
            "\n## 输出契约（story_bible 等）\n"
            "必须输出含 story_bible、character_system、world_system、emotion_system、"
            "originality_report 的 JSON 对象。\n"
            "story_bible 必填：drama_title、logline、synopsis{{short,full}}、adapt_source、"
            "world_rules{{setting_summary,root_rules,power_structure}}、characters（≥1）、"
            "relationship_map、series_structure"
            "{{main_storyline,six_stage_structure(6项),conflict_escalation_chain,"
            "major_reversal_positions,paywall_distribution,foreshadowing_table,"
            "series_emotion_curve}}。\n"
            "characters[].role_type 仅允许 protagonist|antagonist|supporting；"
            "world_rules.root_rules 为字符串数组；power_structure 为字符串。\n"
        )

    return (
        f"{skill_body}\n\n"
        f"## 用户输入\n"
        f"{json.dumps(user_ctx, ensure_ascii=False)}\n"
        f"{contract_hint}\n"
        f"请只输出合法 JSON（不要 Markdown 代码块）。"
    )


def _prompt_project_settings(project: V3Project) -> dict[str, Any]:
    """提示词用 settings 投影：保留模板种子，避免塞入过大无关字段。"""
    settings = _settings_for_normalize(project)
    out: dict[str, Any] = {}
    for key in (
        "title",
        "preset_theme_code",
        "genre_matrix",
        "audience_channel",
        "protagonist_structure",
        "flavor_tags",
        "episode_count",
        "template_seed",
    ):
        if key in settings and settings[key] not in (None, "", {}):
            out[key] = settings[key]
    return out


def _map_payloads(*, writes: list[str], raw_text: str) -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise GenerationError(f"LLM 返回非 JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise GenerationError("LLM 返回必须是 JSON 对象")

    if len(writes) == 1:
        key = writes[0]
        # 允许整包即单产物，或 {"project_brief": {...}}
        if key in data and isinstance(data[key], dict) and set(data.keys()) == {key}:
            return {key: data[key]}
        return {key: data}

    missing = [key for key in writes if key not in data]
    if missing:
        raise GenerationError(f"LLM 返回缺少产物键: {', '.join(missing)}")

    result: dict[str, dict[str, Any]] = {}
    for key in writes:
        value = data[key]
        if not isinstance(value, dict):
            raise GenerationError(f"产物 {key} 必须是 JSON 对象")
        result[key] = value
    return result


def _default_llm_call(prompt: str, *, role: str = "") -> str:
    from apps.drama.orchestrator.llm_router import (
        chat_with_failover,
        get_failover_call_context,
    )
    from apps.drama.services.llm_config_service import LlmConfigService
    from apps.drama.services.llm_provider import LlmProvider, LlmProviderError, LlmProviderStatus

    system_prompt = "你是短剧创作助手，只输出合法 JSON。"
    ctx = get_failover_call_context()
    try:
        if ctx is not None:
            response = chat_with_failover(
                role_key=role or "",
                system_prompt=system_prompt,
                user_prompt=prompt,
                owner=ctx.owner,
                v3_command_run=ctx.run,
                v3_project=ctx.project,
            )
        else:
            # 无 generate 上下文时保持单跳（单测直接调 _default_llm_call）
            cfg = (
                LlmConfigService.resolve_for_role(role)
                if role
                else LlmConfigService.resolve()
            )
            if (
                cfg.source != "db_role_mapping"
                and LlmProvider.status() != LlmProviderStatus.ENABLED
            ):
                raise GenerationError(_PROVIDER_HINT)
            if not cfg.base_url or not cfg.api_key:
                raise GenerationError(_PROVIDER_HINT)
            response = LlmProvider.chat_completion(
                system_prompt=system_prompt,
                user_prompt=prompt,
                json_mode=True,
                config=cfg,
            )
    except LlmProviderError as exc:
        msg = str(exc) or ""
        # 链上无可调用 provider（含空 id hop）时保持旧友好提示
        if "已尝试供应商" in msg and "(无)" in msg:
            raise GenerationError(_PROVIDER_HINT) from exc
        raise GenerationError(msg or _PROVIDER_HINT) from exc

    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GenerationError("LLM 响应格式异常") from exc
    if not isinstance(content, str) or not content.strip():
        raise GenerationError("LLM 响应为空")
    return content
