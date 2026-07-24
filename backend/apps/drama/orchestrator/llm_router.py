# -*- coding: utf-8 -*-
"""V3 LLM 主备链路由：按 resolve_chain 调用并写 V3FailoverAttempt。"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import Any, Callable, Iterator

from apps.drama.models import DramaLlmCallLog, DramaLlmProvider, V3FailoverAttempt
from apps.drama.orchestrator.failover_policy import classify_provider_error, resolve_chain
from apps.drama.orchestrator.provider_keys import ProviderKeySlot, iter_provider_key_slots
from apps.drama.services.llm_config_service import ResolvedLlmConfig
from apps.drama.services.llm_provider import LlmProvider, LlmProviderError

_ERROR_MESSAGE_MAX_LEN = 500


@dataclass(frozen=True)
class FailoverCallContext:
    """execute_generation 注入的 owner/run/project，供 _default_llm_call 写 attempt。"""

    owner: Any
    run: Any
    project: Any


_failover_call_context: ContextVar[FailoverCallContext | None] = ContextVar(
    "failover_call_context", default=None
)


def get_failover_call_context() -> FailoverCallContext | None:
    return _failover_call_context.get()


@contextmanager
def failover_call_scope(*, owner, run, project) -> Iterator[None]:
    token = _failover_call_context.set(
        FailoverCallContext(owner=owner, run=run, project=project)
    )
    try:
        yield
    finally:
        _failover_call_context.reset(token)


def _sanitize_error_message(message: str, *, redact_secrets: list[str] | None = None) -> str:
    text = (message or "").strip()
    for secret in redact_secrets or []:
        if secret and secret in text:
            text = text.replace(secret, "[REDACTED]")
    if len(text) <= _ERROR_MESSAGE_MAX_LEN:
        return text
    return text[:_ERROR_MESSAGE_MAX_LEN]


def _bind_latest_call_log(v3_command_run) -> DramaLlmCallLog | None:
    if v3_command_run is None:
        return None
    return (
        DramaLlmCallLog.objects.filter(v3_command_run=v3_command_run)
        .order_by("-created_at")
        .first()
    )


def _exhausted_error(tried_names: list[str]) -> LlmProviderError:
    if tried_names:
        names = "、".join(tried_names)
    else:
        names = "(无)"
    return LlmProviderError(f"已尝试供应商：{names}")


def _config_with_key(config: ResolvedLlmConfig, api_key: str) -> ResolvedLlmConfig:
    return replace(config, api_key=api_key)


def _key_slots_for_hop(
    provider: DramaLlmProvider, hop_config: ResolvedLlmConfig
) -> list[ProviderKeySlot]:
    slots = iter_provider_key_slots(provider)
    if slots:
        return slots
    # 无主/附加 Key 时回退 hop.config（兼容仅 env 注入场景）
    key = (hop_config.api_key or "").strip()
    if not key:
        return []
    return [ProviderKeySlot(label="主密钥", api_key=key, is_primary=True)]


def chat_with_failover(
    *,
    role_key: str,
    system_prompt: str,
    user_prompt: str,
    owner,
    v3_command_run=None,
    v3_project=None,
    json_mode: bool = True,
    chat_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict:
    """返回与 LlmProvider.chat_completion 相同结构的 response dict。

    链耗尽时 raise LlmProviderError，message 含中文「已尝试供应商」与名称列表。
    同一 ProviderHop 内先轮询主 Key + 附加 Key，可切换错误才换下一供应商。
    """
    invoke = chat_fn or LlmProvider.chat_completion
    hops = resolve_chain(role_key)
    tried_names: list[str] = []
    last_exc: BaseException | None = None

    for hop in hops:
        if not hop.provider_id:
            display_name = hop.provider_name or "环境配置"
            tried_names.append(display_name)
            try:
                response = invoke(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    json_mode=json_mode,
                    config=hop.config,
                )
            except Exception as exc:
                _error_code, is_switchable = classify_provider_error(exc)
                if not is_switchable:
                    raise
                last_exc = exc
                continue
            return response

        provider = DramaLlmProvider.objects.filter(pk=hop.provider_id).first()
        if provider is None:
            continue

        display_name = hop.provider_name or provider.name or hop.provider_id
        tried_names.append(display_name)
        slots = _key_slots_for_hop(provider, hop.config)
        if not slots:
            continue

        hop_exhausted_switchable = False
        for slot in slots:
            cfg = _config_with_key(hop.config, slot.api_key)
            try:
                response = invoke(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    json_mode=json_mode,
                    config=cfg,
                )
            except Exception as exc:
                error_code, is_switchable = classify_provider_error(exc)
                msg = _sanitize_error_message(
                    f"[{slot.label}] {exc}",
                    redact_secrets=[slot.api_key],
                )
                V3FailoverAttempt.objects.create(
                    owner=owner,
                    v3_command_run=v3_command_run,
                    v3_project=v3_project,
                    role_key=role_key,
                    provider=provider,
                    attempt_index=hop.attempt_index,
                    status=(
                        V3FailoverAttempt.Status.FAILED_SWITCHABLE
                        if is_switchable
                        else V3FailoverAttempt.Status.FAILED_TERMINAL
                    ),
                    error_code=error_code,
                    error_message=msg,
                )
                if not is_switchable:
                    raise
                last_exc = exc
                hop_exhausted_switchable = True
                continue

            V3FailoverAttempt.objects.create(
                owner=owner,
                v3_command_run=v3_command_run,
                v3_project=v3_project,
                role_key=role_key,
                provider=provider,
                attempt_index=hop.attempt_index,
                status=V3FailoverAttempt.Status.SUCCEEDED,
                llm_call_log=_bind_latest_call_log(v3_command_run),
            )
            return response

        if hop_exhausted_switchable:
            continue

    err = _exhausted_error(tried_names)
    if last_exc is not None:
        raise err from last_exc
    raise err
