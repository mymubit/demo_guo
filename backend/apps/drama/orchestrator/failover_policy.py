# -*- coding: utf-8 -*-
"""V3 LLM 主备链解析与错误可切换判定。"""
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
    """主 provider + backup_provider_ids 去重保序；跳过不存在 id；无映射则单跳 active/resolve。"""
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
    """返回 (error_code, is_switchable)。"""
    root = _root_cause(exc)
    if isinstance(root, TimeoutError):
        return "timeout", True
    if isinstance(root, requests.exceptions.Timeout):
        return "timeout", True
    if isinstance(root, (ConnectionError, requests.exceptions.ConnectionError)):
        return "connection_error", True

    message = str(exc)

    if isinstance(exc, LlmProviderError):
        if "已禁用" in message:
            return "provider_disabled", True
        if "配置不完整" in message:
            return "provider_misconfigured", True
        if message.startswith("LLM 不可用:"):
            lowered = message.lower()
            if "disabled" in lowered:
                return "provider_disabled", True
            if "misconfigured" in lowered:
                return "provider_misconfigured", True

        http_match = _HTTP_STATUS_RE.match(message)
        if http_match:
            return _http_error_code(int(http_match.group(1)))

        if message == "LLM 流式响应为空":
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
