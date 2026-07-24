# Review package Task 2
Base: Task1 complete working tree
Head: after Task 2
Scope: ONLY new failover_policy files (ignore unrelated uncommitted phase-1)

## Files
?? backend/apps/drama/orchestrator/failover_policy.py
?? backend/apps/drama/tests/test_v3_failover_policy.py

## failover_policy.py
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
## test_v3_failover_policy.py
```python

# -*- coding: utf-8 -*-
"""P2-W1 Task 2锛歠ailover_policy 閾捐В鏋?+ 閿欒鍙垏鎹㈠垽瀹氥€?""
from __future__ import annotations

import uuid

from django.test import TestCase

from apps.drama.models import DramaLlmProvider, V3RoleModelMapping
from apps.drama.orchestrator.failover_policy import (
    classify_provider_error,
    resolve_chain,
)
from apps.drama.services.llm_provider import LlmProviderError
from apps.drama.services.secret_crypto import encrypt_secret


def _make_provider(**overrides) -> DramaLlmProvider:
    data = {
        "name": "provider",
        "base_url": "https://llm.example/v1",
        "model_name": "gpt-test",
        "api_key_encrypted": encrypt_secret("sk-test"),
        "temperature": 0.7,
        "max_tokens": 4096,
        "is_enabled": True,
        "is_active": False,
    }
    data.update(overrides)
    return DramaLlmProvider.objects.create(**data)


class FailoverPolicyTests(TestCase):
    def test_resolve_chain_primary_then_backups_deduped(self) -> None:
        p1 = _make_provider(name="P1", is_active=True)
        p2 = _make_provider(name="P2", base_url="https://p2.example/v1")
        p3 = _make_provider(name="P3", base_url="https://p3.example/v1")
        V3RoleModelMapping.objects.create(
            role_key="drama-script-writer",
            provider=p1,
            backup_provider_ids=[str(p2.id), str(p1.id), str(p3.id)],
        )

        hops = resolve_chain("drama-script-writer")

        self.assertEqual(len(hops), 3)
        self.assertEqual([h.provider_id for h in hops], [str(p1.id), str(p2.id), str(p3.id)])
        self.assertEqual([h.provider_name for h in hops], ["P1", "P2", "P3"])
        self.assertEqual([h.attempt_index for h in hops], [0, 1, 2])
        self.assertEqual(hops[0].config.base_url, "https://llm.example/v1")
        self.assertEqual(hops[1].config.base_url, "https://p2.example/v1")

    def test_resolve_chain_skips_missing_backup_ids(self) -> None:
        p1 = _make_provider(name="Primary", is_active=True)
        missing_id = str(uuid.uuid4())
        V3RoleModelMapping.objects.create(
            role_key="drama-topic-director",
            provider=p1,
            backup_provider_ids=[missing_id],
        )

        hops = resolve_chain("drama-topic-director")

        self.assertEqual(len(hops), 1)
        self.assertEqual(hops[0].provider_id, str(p1.id))

    def test_resolve_chain_no_mapping_single_active_hop(self) -> None:
        active = _make_provider(name="Active", is_active=True)
        _make_provider(name="Inactive")

        hops = resolve_chain("drama-script-writer")

        self.assertEqual(len(hops), 1)
        self.assertEqual(hops[0].provider_id, str(active.id))
        self.assertEqual(hops[0].provider_name, "Active")
        self.assertEqual(hops[0].attempt_index, 0)
        self.assertTrue(hops[0].config.enabled)

    def test_resolve_chain_uses_mapping_temperature_for_all_hops(self) -> None:
        p1 = _make_provider(name="P1", temperature=0.9, max_tokens=8192, is_active=True)
        p2 = _make_provider(name="P2", temperature=0.1, max_tokens=512)
        V3RoleModelMapping.objects.create(
            role_key="drama-script-writer",
            provider=p1,
            temperature=0.25,
            max_tokens=2048,
            backup_provider_ids=[str(p2.id)],
        )

        hops = resolve_chain("drama-script-writer")

        self.assertEqual(hops[0].config.temperature, 0.25)
        self.assertEqual(hops[0].config.max_tokens, 2048)
        self.assertEqual(hops[1].config.temperature, 0.25)
        self.assertEqual(hops[1].config.max_tokens, 2048)

    def test_classify_timeout_switchable(self) -> None:
        code, ok = classify_provider_error(TimeoutError("x"))
        self.assertTrue(ok)
        self.assertEqual(code, "timeout")

    def test_classify_connection_error_switchable(self) -> None:
        code, ok = classify_provider_error(ConnectionError("refused"))
        self.assertTrue(ok)
        self.assertEqual(code, "connection_error")

    def test_classify_http_429_switchable(self) -> None:
        code, ok = classify_provider_error(LlmProviderError("LLM HTTP 429: rate limited"))
        self.assertTrue(ok)
        self.assertEqual(code, "http_429")

    def test_classify_http_401_switchable(self) -> None:
        code, ok = classify_provider_error(LlmProviderError("LLM HTTP 401: unauthorized"))
        self.assertTrue(ok)
        self.assertEqual(code, "http_401")

    def test_classify_http_500_switchable(self) -> None:
        code, ok = classify_provider_error(LlmProviderError("LLM HTTP 502: bad gateway"))
        self.assertTrue(ok)
        self.assertEqual(code, "http_502")

    def test_classify_disabled_switchable(self) -> None:
        code, ok = classify_provider_error(
            LlmProviderError("LLM 宸茬鐢紙鍚庡彴鏈惎鐢ㄤ笖 LLM_ENABLED=false锛?)
        )
        self.assertTrue(ok)
        self.assertEqual(code, "provider_disabled")

    def test_classify_misconfigured_switchable(self) -> None:
        code, ok = classify_provider_error(
            LlmProviderError("LLM 閰嶇疆涓嶅畬鏁达紝璇峰湪鍚庡彴濉啓 Base URL 涓?API Key")
        )
        self.assertTrue(ok)
        self.assertEqual(code, "provider_misconfigured")

    def test_classify_http_400_not_switchable(self) -> None:
        code, ok = classify_provider_error(LlmProviderError("LLM HTTP 400: bad request"))
        self.assertFalse(ok)
        self.assertEqual(code, "http_400")

    def test_classify_empty_stream_not_switchable(self) -> None:
        code, ok = classify_provider_error(LlmProviderError("LLM 娴佸紡鍝嶅簲涓虹┖"))
        self.assertFalse(ok)
        self.assertEqual(code, "empty_response")

    def test_classify_generic_not_switchable(self) -> None:
        code, ok = classify_provider_error(ValueError("bad json later"))
        self.assertFalse(ok)
        self.assertEqual(code, "unknown")

    def test_classify_wrapped_timeout_switchable(self) -> None:
        code, ok = classify_provider_error(
            LlmProviderError("HTTPSConnectionPool(host='x'): Read timed out.")
        )
        self.assertTrue(ok)
        self.assertEqual(code, "timeout")

```

