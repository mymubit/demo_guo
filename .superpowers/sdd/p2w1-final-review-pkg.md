# P2-W1 whole-milestone review package
Minors carried from task reviews: T2 403/408 gaps; T3 empty-chain/ValueError/weak call-log; T6 no latency on attempts.

## File list
backend/apps/drama/models.py
backend/apps/drama/migrations/0020_v3_failover_attempt_and_backup_ids.py
backend/apps/drama/orchestrator/failover_policy.py
backend/apps/drama/orchestrator/llm_router.py
backend/apps/drama/skills_bridge/executor.py
backend/apps/drama/api/v3/serializers.py
backend/apps/drama/api/v3/models_service.py
backend/apps/drama/api/v3/logs_views.py
backend/apps/drama/tests/test_v3_failover_models.py
backend/apps/drama/tests/test_v3_failover_policy.py
backend/apps/drama/tests/test_v3_llm_router.py
backend/apps/drama/tests/test_v3_failover_executor.py
backend/apps/drama/tests/test_v3_models_api.py
backend/apps/drama/tests/test_v3_logs_api.py
backend/apps/drama/tests/test_v3_provider_test.py
frontend/src/pages/LogsPage.tsx
frontend/src/pages/LogsPage.test.tsx
frontend/src/types/v3/domain.ts
docs/contracts/v3/openapi.yaml
docs/superpowers/baselines/2026-07-23-p2-w1-failover-runtime-acceptance.md

## Status
 M backend/apps/drama/models.py ?? backend/apps/drama/api/v3/logs_views.py ?? backend/apps/drama/api/v3/models_service.py ?? backend/apps/drama/api/v3/serializers.py ?? backend/apps/drama/migrations/0020_v3_failover_attempt_and_backup_ids.py ?? backend/apps/drama/orchestrator/failover_policy.py ?? backend/apps/drama/orchestrator/llm_router.py ?? backend/apps/drama/skills_bridge/executor.py ?? backend/apps/drama/tests/test_v3_failover_executor.py ?? backend/apps/drama/tests/test_v3_failover_models.py ?? backend/apps/drama/tests/test_v3_failover_policy.py ?? backend/apps/drama/tests/test_v3_llm_router.py ?? backend/apps/drama/tests/test_v3_logs_api.py ?? backend/apps/drama/tests/test_v3_models_api.py ?? backend/apps/drama/tests/test_v3_provider_test.py ?? docs/contracts/v3/openapi.yaml ?? docs/superpowers/baselines/2026-07-23-p2-w1-failover-runtime-acceptance.md ?? frontend/src/pages/LogsPage.test.tsx ?? frontend/src/pages/LogsPage.tsx ?? frontend/src/types/v3/domain.ts

## New/untracked content samples included below for key new modules

### backend/apps/drama/orchestrator/failover_policy.py
```python

# -*- coding: utf-8 -*-
"""V3 LLM 涓诲閾捐В鏋愪笌閿欒鍙垏鎹㈠垽瀹氥€?""
from __future__ import annotations

import re
from dataclasses import dataclass

import requests

from apps.drama.models import DramaLlmProvider, V3RoleModelMapping
from apps.drama.services.llm_config_service import LlmConfigService, ResolvedLlmConfig
from apps.drama.services.llm_provider import LlmProviderError
from apps.drama.services.secret_crypto import decrypt_secret

_HTTP_STATUS_RE = re.compile(r"^LLM HTTP (\d{3})\b")
_SWITCHABLE_HTTP_STATUSES = frozenset({401, 403, 408, 429})


@dataclass(frozen=True)
class ProviderHop:
    provider_id: str
    provider_name: str
    config: ResolvedLlmConfig
    attempt_index: int


def _config_from_provider(
    provider: DramaLlmProvider,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> ResolvedLlmConfig:
    api_key = decrypt_secret(provider.api_key_encrypted) or ""
    resolved_temperature = (
        float(temperature)
        if temperature is not None
        else float(provider.temperature)
    )
    resolved_max_tokens = (
        int(max_tokens)
        if max_tokens is not None
        else int(provider.max_tokens)
    )
    return ResolvedLlmConfig(
        enabled=True,
        base_url=(provider.base_url or "").strip(),
        api_key=api_key,
        model=(provider.model_name or "").strip() or "gpt-4o-mini",
        temperature=resolved_temperature,
        max_tokens=resolved_max_tokens,
        source="db_role_mapping",
    )


def _active_provider() -> DramaLlmProvider | None:
    return (
        DramaLlmProvider.objects.filter(is_active=True, is_enabled=True)
        .order_by("-updated_at")
        .first()
    )


def _single_hop_from_resolve() -> list[ProviderHop]:
    active = _active_provider()
    if active:
        cfg = LlmConfigService.resolve()
        return [
            ProviderHop(
                provider_id=str(active.id),
                provider_name=active.name,
                config=cfg,
                attempt_index=0,
            )
        ]
    cfg = LlmConfigService.resolve()
    return [
        ProviderHop(
            provider_id="",
            provider_name="",
            config=cfg,
            attempt_index=0,
        )
    ]


def resolve_chain(role_key: str) -> list[ProviderHop]:
    """涓?provider + backup_provider_ids 鍘婚噸淇濆簭锛涜烦杩囦笉瀛樺湪 id锛涙棤鏄犲皠鍒欏崟璺?active/resolve銆?""
    key = (role_key or "").strip()
    if not key:
        return _single_hop_from_resolve()

    mapping = (
        V3RoleModelMapping.objects.select_related("provider")
        .filter(role_key=key)
        .first()
    )
    if mapping is None:
        return _single_hop_from_resolve()

    ordered_ids: list[str] = [str(mapping.provider_id)]
    for raw_id in mapping.backup_provider_ids or []:
        provider_id = str(raw_id).strip()
        if not provider_id or provider_id in ordered_ids:
            continue
        ordered_ids.append(provider_id)

    providers_by_id = {
        str(provider.id): provider
        for provider in DramaLlmProvider.objects.filter(id__in=ordered_ids)
    }

    hops: list[ProviderHop] = []
    for provider_id in ordered_ids:
        provider = providers_by_id.get(provider_id)
        if provider is None:
            continue
        hops.append(
            ProviderHop(
                provider_id=provider_id,
                provider_name=provider.name,
                config=_config_from_provider(
                    provider,
                    temperature=mapping.temperature,
                    max_tokens=mapping.max_tokens,
                ),
                attempt_index=len(hops),
            )
        )

    if hops:
        return hops
    return _single_hop_from_resolve()


def _root_cause(exc: BaseException) -> BaseException:
    current = exc
    while current.__cause__ is not None:
        current = current.__cause__
    return current


def _is_timeout_message(message: str) -> bool:
    lowered = message.lower()
    return "timed out" in lowered or "timeout" in lowered


def _is_connection_message(message: str) -> bool:
    lowered = message.lower()
    markers = (
        "connection error",
        "connection refused",
        "failed to establish a new connection",
        "name or service not known",
        "getaddrinfo failed",
        "connection aborted",
        "connection reset",
    )
    return any(marker in lowered for marker in markers)


def _http_error_code(status_code: int) -> tuple[str, bool]:
    if status_code in _SWITCHABLE_HTTP_STATUSES or status_code >= 500:
        return f"http_{status_code}", True
    return f"http_{status_code}", False


def classify_provider_error(exc: BaseException) -> tuple[str, bool]:
    """杩斿洖 (error_code, is_switchable)銆?""
    root = _root_cause(exc)
    if isinstance(root, TimeoutError):
        return "timeout", True
    if isinstance(root, requests.exceptions.Timeout):
        return "timeout", True
    if isinstance(root, (ConnectionError, requests.exceptions.ConnectionError)):
        return "connection_error", True

    message = str(exc)

    if isinstance(exc, LlmProviderError):
        if "宸茬鐢? in message:
            return "provider_disabled", True
        if "閰嶇疆涓嶅畬鏁? in message:
            return "provider_misconfigured", True
        if message.startswith("LLM 涓嶅彲鐢?"):
            lowered = message.lower()
            if "disabled" in lowered:
                return "provider_disabled", True
            if "misconfigured" in lowered:
                return "provider_misconfigured", True

        http_match = _HTTP_STATUS_RE.match(message)
        if http_match:
            return _http_error_code(int(http_match.group(1)))

        if message == "LLM 娴佸紡鍝嶅簲涓虹┖":
            return "empty_response", False

        if _is_timeout_message(message):
            return "timeout", True
        if _is_connection_message(message):
            return "connection_error", True

    if _is_timeout_message(message):
        return "timeout", True
    if _is_connection_message(message):
        return "connection_error", True

    return "unknown", False

```


### backend/apps/drama/orchestrator/llm_router.py
```python

# -*- coding: utf-8 -*-
"""V3 LLM 涓诲閾捐矾鐢憋細鎸?resolve_chain 璋冪敤骞跺啓 V3FailoverAttempt銆?""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable, Iterator

from apps.drama.models import DramaLlmCallLog, DramaLlmProvider, V3FailoverAttempt
from apps.drama.orchestrator.failover_policy import classify_provider_error, resolve_chain
from apps.drama.services.llm_provider import LlmProvider, LlmProviderError

_ERROR_MESSAGE_MAX_LEN = 500


@dataclass(frozen=True)
class FailoverCallContext:
    """execute_generation 娉ㄥ叆鐨?owner/run/project锛屼緵 _default_llm_call 鍐?attempt銆?""

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


def _sanitize_error_message(message: str) -> str:
    text = (message or "").strip()
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
        names = "銆?.join(tried_names)
    else:
        names = "(鏃?"
    return LlmProviderError(f"宸插皾璇曚緵搴斿晢锛歿names}")


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
    """杩斿洖涓?LlmProvider.chat_completion 鐩稿悓缁撴瀯鐨?response dict銆?

    閾捐€楀敖鏃?raise LlmProviderError锛宮essage 鍚腑鏂囥€屽凡灏濊瘯渚涘簲鍟嗐€嶄笌鍚嶇О鍒楄〃銆?
    """
    invoke = chat_fn or LlmProvider.chat_completion
    hops = resolve_chain(role_key)
    tried_names: list[str] = []
    last_exc: BaseException | None = None

    for hop in hops:
        if not hop.provider_id:
            continue
        provider = DramaLlmProvider.objects.filter(pk=hop.provider_id).first()
        if provider is None:
            continue

        display_name = hop.provider_name or provider.name or hop.provider_id
        tried_names.append(display_name)

        try:
            response = invoke(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_mode=json_mode,
                config=hop.config,
            )
        except Exception as exc:
            error_code, is_switchable = classify_provider_error(exc)
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
                error_message=_sanitize_error_message(str(exc)),
            )
            if not is_switchable:
                raise
            last_exc = exc
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

    err = _exhausted_error(tried_names)
    if last_exc is not None:
        raise err from last_exc
    raise err

```

