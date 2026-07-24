# -*- coding: utf-8 -*-
"""P2-W1 Task 3：llm_router 按链调用并写 FailoverAttempt。"""
from __future__ import annotations

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.drama.models import (
    DramaLlmCallLog,
    DramaLlmProvider,
    V3CommandRun,
    V3FailoverAttempt,
    V3Project,
    V3RoleModelMapping,
)
from apps.drama.orchestrator.failover_policy import ProviderHop
from apps.drama.orchestrator.llm_router import chat_with_failover
from apps.drama.services.llm_config_service import ResolvedLlmConfig
from apps.drama.services.llm_provider import LlmProviderError
from apps.drama.services.secret_crypto import encrypt_secret
from apps.drama.tests.helpers import SKILLS_ROOT


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


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class LlmRouterTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user("router-u", password="x")
        self.project = V3Project.objects.create(
            owner=self.user,
            title="t",
            entry_type="original",
            stage="topic",
        )
        self.run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.RUNNING,
        )

    def test_failover_to_backup_on_switchable_error(self) -> None:
        p1 = _make_provider(name="P1", is_active=True)
        p2 = _make_provider(name="P2", base_url="https://p2.example/v1")
        V3RoleModelMapping.objects.create(
            role_key="drama-script-writer",
            provider=p1,
            backup_provider_ids=[str(p2.id)],
        )
        fake_resp = {"choices": [{"message": {"content": '{"ok": true}'}}]}
        calls: list[str] = []

        def chat_fn(*, system_prompt, user_prompt, json_mode=True, config=None, **_kwargs):
            calls.append(config.base_url if config else "")
            if len(calls) == 1:
                raise LlmProviderError("LLM HTTP 503: unavailable")
            return fake_resp

        resp = chat_with_failover(
            role_key="drama-script-writer",
            system_prompt="sys",
            user_prompt="usr",
            owner=self.user,
            v3_command_run=self.run,
            v3_project=self.project,
            chat_fn=chat_fn,
        )

        self.assertEqual(resp, fake_resp)
        self.assertEqual(len(calls), 2)
        attempts = list(V3FailoverAttempt.objects.order_by("attempt_index"))
        self.assertEqual(len(attempts), 2)
        self.assertEqual(
            [a.status for a in attempts],
            [
                V3FailoverAttempt.Status.FAILED_SWITCHABLE,
                V3FailoverAttempt.Status.SUCCEEDED,
            ],
        )
        self.assertEqual(attempts[0].provider_id, p1.id)
        self.assertEqual(attempts[1].provider_id, p2.id)
        self.assertEqual(attempts[0].error_code, "http_503")

    def test_exhausted_chain_raises_with_zh_summary(self) -> None:
        p1 = _make_provider(name="P1", is_active=True)
        p2 = _make_provider(name="P2")
        V3RoleModelMapping.objects.create(
            role_key="drama-script-writer",
            provider=p1,
            backup_provider_ids=[str(p2.id)],
        )

        def chat_fn(**_kwargs):
            raise LlmProviderError("LLM HTTP 503: unavailable")

        with self.assertRaises(LlmProviderError) as ctx:
            chat_with_failover(
                role_key="drama-script-writer",
                system_prompt="sys",
                user_prompt="usr",
                owner=self.user,
                v3_command_run=self.run,
                v3_project=self.project,
                chat_fn=chat_fn,
            )

        self.assertIn("已尝试供应商", str(ctx.exception))
        self.assertIn("P1", str(ctx.exception))
        self.assertIn("P2", str(ctx.exception))
        attempts = list(V3FailoverAttempt.objects.order_by("attempt_index"))
        self.assertEqual(len(attempts), 2)
        self.assertTrue(
            all(a.status == V3FailoverAttempt.Status.FAILED_SWITCHABLE for a in attempts)
        )

    def test_terminal_error_stops_without_backup(self) -> None:
        p1 = _make_provider(name="P1", is_active=True)
        p2 = _make_provider(name="P2")
        V3RoleModelMapping.objects.create(
            role_key="drama-script-writer",
            provider=p1,
            backup_provider_ids=[str(p2.id)],
        )
        calls = 0

        def chat_fn(**_kwargs):
            nonlocal calls
            calls += 1
            raise LlmProviderError("LLM 流式响应为空")

        with self.assertRaises(LlmProviderError) as ctx:
            chat_with_failover(
                role_key="drama-script-writer",
                system_prompt="sys",
                user_prompt="usr",
                owner=self.user,
                v3_command_run=self.run,
                v3_project=self.project,
                chat_fn=chat_fn,
            )

        self.assertEqual(str(ctx.exception), "LLM 流式响应为空")
        self.assertEqual(calls, 1)
        attempts = list(V3FailoverAttempt.objects.all())
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].status, V3FailoverAttempt.Status.FAILED_TERMINAL)
        self.assertEqual(attempts[0].error_code, "empty_response")
        self.assertEqual(attempts[0].provider_id, p1.id)

    def test_success_binds_latest_call_log_for_run(self) -> None:
        p1 = _make_provider(name="P1", is_active=True)
        V3RoleModelMapping.objects.create(
            role_key="drama-script-writer",
            provider=p1,
        )
        log = DramaLlmCallLog.objects.create(
            v3_command_run=self.run,
            v3_project=self.project,
            role="drama-script-writer",
            status=DramaLlmCallLog.Status.SUCCESS,
            response_text="{}",
        )

        def chat_fn(**_kwargs):
            return {"choices": [{"message": {"content": "{}"}}]}

        chat_with_failover(
            role_key="drama-script-writer",
            system_prompt="sys",
            user_prompt="usr",
            owner=self.user,
            v3_command_run=self.run,
            v3_project=self.project,
            chat_fn=chat_fn,
        )

        attempt = V3FailoverAttempt.objects.get()
        self.assertEqual(attempt.status, V3FailoverAttempt.Status.SUCCEEDED)
        self.assertEqual(attempt.llm_call_log_id, log.id)

    def test_env_only_hop_succeeds_without_failover_attempt(self) -> None:
        fake_cfg = ResolvedLlmConfig(
            enabled=True,
            base_url="https://env.example/v1",
            api_key="sk-env",
            model="gpt-env",
            temperature=0.7,
            max_tokens=4096,
            source="env",
        )
        hops = [
            ProviderHop(
                provider_id="",
                provider_name="",
                config=fake_cfg,
                attempt_index=0,
            )
        ]
        fake_resp = {"choices": [{"message": {"content": '{"ok": true}'}}]}

        def chat_fn(*, system_prompt, user_prompt, json_mode=True, config=None, **_kwargs):
            self.assertEqual(config, fake_cfg)
            return fake_resp

        with patch(
            "apps.drama.orchestrator.llm_router.resolve_chain",
            return_value=hops,
        ):
            resp = chat_with_failover(
                role_key="drama-script-writer",
                system_prompt="sys",
                user_prompt="usr",
                owner=self.user,
                v3_command_run=self.run,
                v3_project=self.project,
                chat_fn=chat_fn,
            )

        self.assertEqual(resp, fake_resp)
        self.assertEqual(V3FailoverAttempt.objects.count(), 0)
