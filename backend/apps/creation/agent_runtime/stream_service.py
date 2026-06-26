# -*- coding: utf-8 -*-
"""独立 Agent 流式执行（SSE 主链路）。"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.runtime import workspace_index_for_agent
from apps.creation.agent_runtime.chunk_service import (
    last_chunk_index,
    resolve_chunk_kind,
    upsert_chunk,
)
from apps.creation.agent_runtime.agent_billing import charge_agent_run, ensure_agent_chargeable, refund_agent_run
from apps.creation.agent_runtime.independent_service import AgentRuntimeError, IndependentAgentService
from apps.creation.models import AgentExecutionRun, Project, SkillGenerationLog
from apps.creation.monitoring.execution_run_service import AgentExecutionRunService
from apps.skill.llm.chat_stream import iter_chat_completion_stream
from apps.skill.llm.usage_log import llm_usage_scope
from apps.skill.models import LlmUsageLog
from apps.skill.skills.invoker_stream import (
    PROTOCOL_VERSION,
    WATCHDOG_SECONDS,
    StreamEventType,
    TokenThrottler,
    format_sse,
    new_trace_id,
    sse_heartbeat,
)
from apps.skill.skills.streaming_json_parser import IncrementalJsonArrayParser, extract_episode_number

logger = logging.getLogger(__name__)


def _get_stream_config(agent_id: str) -> Optional[Dict[str, Any]]:
    from apps.drama.skills_registry import build_agent_stream_config

    return build_agent_stream_config().get(agent_id)


def _fallback_provider_ids(route) -> List[str]:
    rules = getattr(route, "routing_rules", None) or {}
    raw = rules.get("fallback_provider_id") or rules.get("fallback_provider_ids") or []
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return []


class AgentStreamService:
    @staticmethod
    def assert_can_stream(project: Project, user, agent_id: str) -> None:
        IndependentAgentService.assert_project_owner(project, user)
        running = IndependentAgentService.running_run(project)
        if running:
            raise AgentRuntimeError("该项目已有 Agent 正在执行，请稍后再试")
        agent = AgentDefinitionService.get_runnable(agent_id)
        contract = agent.input_contract or {}
        missing = []
        for key in contract.get("required_artifacts") or []:
            from apps.creation.artifact_service import get_artifact

            if get_artifact(project, str(key)) in (None, {}, []):
                missing.append(str(key))
        if missing:
            raise AgentRuntimeError(f"缺少必要产物：{', '.join(missing)}")

    @staticmethod
    def resolve_continue_from(project: Project, agent_id: str, params: Dict[str, Any]) -> Optional[int]:
        raw = params.get("continue_from")
        if raw is not None:
            try:
                return int(raw)
            except (TypeError, ValueError):
                pass
        cfg = _get_stream_config(agent_id)
        if not cfg:
            return None
        last = last_chunk_index(project, cfg["kind"])
        if last is None:
            return None
        return last + 1

    @classmethod
    def stream_events(
        cls,
        project: Project,
        user,
        agent_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Generator[str, None, None]:
        params = dict(params or {})
        trace_id = new_trace_id()
        started = time.monotonic()
        run: Optional[AgentExecutionRun] = None
        item_count = 0
        finalize_status = SkillGenerationLog.STATUS_OK
        error_message = ""
        throttler = TokenThrottler()
        last_token_at = time.monotonic()
        saw_first_item = False
        stream_charged = False

        try:
            ensure_agent_chargeable(user, agent_id, params)
            cls.assert_can_stream(project, user, agent_id)
            agent = AgentDefinitionService.get_runnable(agent_id)
            route = AgentDefinitionService.active_route(agent)
            prepared = IndependentAgentService._prepare_prompt(project, agent, params)  # noqa: SLF001
            if not prepared["within_limit"]:
                raise AgentRuntimeError(
                    f"预计输入 tokens 超过上限: {prepared['estimated_prompt_tokens']}/{prepared['max_prompt_tokens']}"
                )

            cache_payload = {
                "agent_id": agent.agent_id,
                "prompt_version": prepared["prompt_version"],
                "params": params,
                "input_keys": prepared["input_artifact_keys"],
            }
            from apps.skill.skills.stream_prompt_cache import get_cached_prompt, set_cached_prompt

            cached_prompts = get_cached_prompt(cache_payload)
            is_cached = cached_prompts is not None
            if cached_prompts:
                system_prompt, user_prompt = cached_prompts
                prepared = {**prepared, "system_prompt": system_prompt, "user_prompt": user_prompt}
            else:
                set_cached_prompt(
                    cache_payload,
                    prepared["system_prompt"],
                    prepared["user_prompt"],
                )

            stream_cfg = _get_stream_config(agent_id)
            chunk_kind = resolve_chunk_kind(
                agent_id,
                str((agent.output_contract or {}).get("artifacts") or [""])[0],
            )
            continue_from = cls.resolve_continue_from(project, agent_id, params)
            array_keys = tuple(stream_cfg.get("array_keys") or ("episodes",)) if stream_cfg else ("episodes",)
            total_episodes = params.get("episode_to") or params.get("script_to") or project.episode_count

            with transaction.atomic():
                locked = Project.objects.select_for_update().get(pk=project.pk)
                if IndependentAgentService.running_run(locked):
                    raise AgentRuntimeError("该项目已有 Agent 正在执行")
                script_from, script_to = IndependentAgentService._script_batch_bounds(params)  # noqa: SLF001
                output_keys = [str(k) for k in (agent.output_contract or {}).get("artifacts") or []]
                run = AgentExecutionRunService.begin_run(
                    locked,
                    agent_id=agent.agent_id,
                    agent_version=agent.version,
                    prompt_version=prepared["prompt_version"],
                    node_index=workspace_index_for_agent(agent.agent_id),
                    script_from=script_from or continue_from,
                    script_to=script_to,
                    input_artifact_keys=prepared["input_artifact_keys"],
                    output_artifact_keys=output_keys,
                    input_snapshot=prepared["input_payload"],
                    rendered_prompt_preview=(prepared["system_prompt"] + "\n\n" + prepared["user_prompt"])[:12000],
                    estimated_prompt_tokens=prepared["estimated_prompt_tokens"],
                    model_name=route.llm_provider.model_name if route.llm_provider else "",
                    provider_name=route.llm_provider.name if route.llm_provider else "",
                    started_by="user",
                    run_params={**params, "stream": True, "trace_id": trace_id},
                    overwrite_mode=IndependentAgentService._resolve_overwrite_mode(agent, params),  # noqa: SLF001
                )
                locked.save(update_fields=["updated_at"])
                project = locked

            try:
                charge_agent_run(user, agent.agent_id, run_id=str(run.id), params=params)
                stream_charged = True
            except Exception as charge_exc:  # noqa: BLE001
                AgentExecutionRunService.finish_run(
                    run,
                    AgentExecutionRun.STATUS_FAILED,
                    error_message=str(charge_exc)[:500],
                )
                raise AgentRuntimeError(str(charge_exc)) from charge_exc

            yield sse_heartbeat()
            yield format_sse(
                StreamEventType.START,
                {
                    "skill_id": agent.agent_id,
                    "agent_id": agent.agent_id,
                    "trace_id": trace_id,
                    "protocol_version": PROTOCOL_VERSION,
                    "total_episodes": int(total_episodes) if total_episodes else None,
                    "continue_from": continue_from,
                    "run_id": str(run.id),
                    "cached": is_cached,
                },
            )

            parser = IncrementalJsonArrayParser(array_keys=array_keys) if stream_cfg else None
            full_text_parts: List[str] = []
            effective_base = int(continue_from or script_from or 1)
            provider_id = str(route.llm_provider_id)
            max_completion = route.max_completion_tokens or route.max_tokens or (agent.runtime_policy or {}).get(
                "max_completion_tokens"
            )

            with llm_usage_scope(
                source_type=LlmUsageLog.SOURCE_AGENT,
                source_key=agent.agent_id,
                project_id=project.id,
                user_id=project.user_id,
                execution_run_id=run.id,
            ):
                for delta, _usage in iter_chat_completion_stream(
                    system_prompt=prepared["system_prompt"],
                    user_prompt=prepared["user_prompt"],
                    temperature=route.temperature,
                    max_tokens=max_completion,
                    provider_id=provider_id,
                    json_mode=True,
                    fallback_provider_ids=_fallback_provider_ids(route),
                ):
                    if time.monotonic() - last_token_at > WATCHDOG_SECONDS:
                        finalize_status = SkillGenerationLog.STATUS_TRUNCATED
                        error_message = "流式生成超时：120s 无新 token"
                        yield format_sse(
                            StreamEventType.ERROR,
                            {"message": error_message, "code": 408, "trace_id": trace_id},
                        )
                        break
                    if delta:
                        last_token_at = time.monotonic()
                        full_text_parts.append(delta)
                        if not saw_first_item:
                            for token_event in throttler.push(delta):
                                yield token_event
                        if parser:
                            for item in parser.feed(delta):
                                item_count += 1
                                saw_first_item = True
                                effective_index = extract_episode_number(
                                    item,
                                    effective_base + item_count - 1,
                                )
                                upsert_chunk(
                                    project,
                                    kind=chunk_kind,
                                    index=effective_index,
                                    data=item,
                                    run=run,
                                )
                                yield format_sse(
                                    StreamEventType.ITEM,
                                    {
                                        "data": item,
                                        "item_index": item_count - 1,
                                        "item_id": str(effective_index),
                                        "effective_index": effective_index,
                                    },
                                )

            if parser and not saw_first_item:
                for item in parser.flush():
                    item_count += 1
                    effective_index = extract_episode_number(item, effective_base + item_count - 1)
                    upsert_chunk(project, kind=chunk_kind, index=effective_index, data=item, run=run)
                    yield format_sse(
                        StreamEventType.ITEM,
                        {
                            "data": item,
                            "item_index": item_count - 1,
                            "item_id": str(effective_index),
                            "effective_index": effective_index,
                        },
                    )

            for token_event in throttler.drain():
                yield token_event

            full_raw = "".join(full_text_parts)
            if finalize_status == SkillGenerationLog.STATUS_OK and full_raw.strip():
                from apps.creation.agent_runtime.json_self_heal import parse_json_with_self_heal

                parsed, heal_attempts = parse_json_with_self_heal(
                    full_raw,
                    agent=agent,
                    system_prompt=prepared["system_prompt"],
                    user_prompt=prepared["user_prompt"],
                    temperature=route.temperature,
                    max_tokens=max_completion,
                    provider_id=provider_id,
                )
                outputs = IndependentAgentService.validate_output(
                    agent,
                    parsed,
                    run_params=dict(run.run_params or {}),
                )
                saved_keys = IndependentAgentService.persist_agent_output(
                    project,
                    agent,
                    run,
                    outputs,
                    prompt_version=prepared["prompt_version"],
                )
                usage = LlmUsageLog.objects.filter(execution_run_id=run.id).order_by("-created_at").first()
                AgentExecutionRunService.finish_run(
                    run,
                    AgentExecutionRun.STATUS_COMPLETED,
                    output_artifact_key=saved_keys[0] if saved_keys else "",
                    output_summary={
                        "outputKeys": saved_keys,
                        "jsonHealAttempts": heal_attempts,
                        "streamItemCount": item_count,
                        "traceId": trace_id,
                    },
                    prompt_tokens=usage.prompt_tokens if usage else None,
                    completion_tokens=usage.completion_tokens if usage else None,
                    total_tokens=usage.total_tokens if usage else None,
                    model_name=usage.model_name if usage else "",
                    provider_name=usage.provider_name if usage else "",
                )
                IndependentAgentService.update_project_status(project)
            elif run and run.status == AgentExecutionRun.STATUS_RUNNING:
                AgentExecutionRunService.finish_run(
                    run,
                    AgentExecutionRun.STATUS_FAILED,
                    error_message=error_message or "流式生成未完成",
                )
                finalize_status = SkillGenerationLog.STATUS_TRUNCATED if error_message else SkillGenerationLog.STATUS_ERROR
                IndependentAgentService.update_project_status(project)
                if stream_charged:
                    refund_agent_run(user, agent.agent_id, run_id=str(run.id))

            duration_ms = int((time.monotonic() - started) * 1000)
            usage = LlmUsageLog.objects.filter(execution_run_id=run.id).order_by("-created_at").first() if run else None
            SkillGenerationLog.objects.create(
                trace_id=trace_id,
                agent_id=agent.agent_id,
                user=user if getattr(user, "is_authenticated", False) else None,
                project=project,
                run=run,
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
                total_tokens=usage.total_tokens if usage else None,
                provider=usage.provider_name if usage else "",
                model=usage.model_name if usage else "",
                duration_ms=duration_ms,
                status=finalize_status,
                error_message=error_message,
            )
            yield format_sse(
                StreamEventType.DONE,
                {
                    "count": item_count,
                    "duration_ms": duration_ms,
                    "finalize_status": finalize_status,
                    "trace_id": trace_id,
                },
            )
        except GeneratorExit:
            if run and run.status == AgentExecutionRun.STATUS_RUNNING:
                AgentExecutionRunService.finish_run(
                    run,
                    AgentExecutionRun.STATUS_PARTIAL,
                    error_message="客户端断开连接",
                )
                SkillGenerationLog.objects.create(
                    trace_id=trace_id,
                    agent_id=agent_id,
                    user=user if getattr(user, "is_authenticated", False) else None,
                    project=project,
                    run=run,
                    duration_ms=int((time.monotonic() - started) * 1000),
                    status=SkillGenerationLog.STATUS_TRUNCATED,
                    error_message="客户端断开连接",
                )
            raise
        except PermissionDenied as exc:
            yield format_sse(
                StreamEventType.ERROR,
                {"message": str(exc), "code": 403, "trace_id": trace_id},
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[AgentStream] failed project=%s agent=%s", project.id, agent_id)
            if run and stream_charged:
                refund_agent_run(user, agent_id, run_id=str(run.id))
            if run and run.status == AgentExecutionRun.STATUS_RUNNING:
                AgentExecutionRunService.finish_run(run, AgentExecutionRun.STATUS_FAILED, error_message=str(exc)[:2000])
                IndependentAgentService.update_project_status(project)
            SkillGenerationLog.objects.create(
                trace_id=trace_id,
                agent_id=agent_id,
                user=user if getattr(user, "is_authenticated", False) else None,
                project=project,
                run=run,
                duration_ms=int((time.monotonic() - started) * 1000),
                status=SkillGenerationLog.STATUS_ERROR,
                error_message=str(exc)[:2000],
            )
            yield format_sse(
                StreamEventType.ERROR,
                {"message": str(exc), "code": 500, "trace_id": trace_id},
            )
