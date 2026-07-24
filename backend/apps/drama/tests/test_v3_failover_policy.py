# -*- coding: utf-8 -*-
"""P2-W1 Task 2：failover_policy 链解析 + 错误可切换判定。"""
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
            LlmProviderError("LLM 已禁用（后台未启用且 LLM_ENABLED=false）")
        )
        self.assertTrue(ok)
        self.assertEqual(code, "provider_disabled")

    def test_classify_misconfigured_switchable(self) -> None:
        code, ok = classify_provider_error(
            LlmProviderError("LLM 配置不完整，请在后台填写 Base URL 与 API Key")
        )
        self.assertTrue(ok)
        self.assertEqual(code, "provider_misconfigured")

    def test_classify_http_400_not_switchable(self) -> None:
        code, ok = classify_provider_error(LlmProviderError("LLM HTTP 400: bad request"))
        self.assertFalse(ok)
        self.assertEqual(code, "http_400")

    def test_classify_empty_stream_not_switchable(self) -> None:
        code, ok = classify_provider_error(LlmProviderError("LLM 流式响应为空"))
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
