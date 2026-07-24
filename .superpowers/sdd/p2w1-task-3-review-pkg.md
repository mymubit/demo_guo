# Review package Task 3 — llm_router only

## llm_router.py
```python
# -*- coding: utf-8 -*-
"""V3 LLM 涓诲閾捐矾鐢憋細鎸?resolve_chain 璋冪敤骞跺啓 V3FailoverAttempt銆?""
from __future__ import annotations

from typing import Any, Callable

from apps.drama.models import DramaLlmCallLog, DramaLlmProvider, V3FailoverAttempt
from apps.drama.orchestrator.failover_policy import classify_provider_error, resolve_chain
from apps.drama.services.llm_provider import LlmProvider, LlmProviderError

_ERROR_MESSAGE_MAX_LEN = 500


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

## test_v3_llm_router.py
```python
# -*- coding: utf-8 -*-
"""P2-W1 Task 3锛歭lm_router 鎸夐摼璋冪敤骞跺啓 FailoverAttempt銆?""
from __future__ import annotations

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
from apps.drama.orchestrator.llm_router import chat_with_failover
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

        self.assertIn("宸插皾璇曚緵搴斿晢", str(ctx.exception))
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
            raise LlmProviderError("LLM 娴佸紡鍝嶅簲涓虹┖")

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

        self.assertEqual(str(ctx.exception), "LLM 娴佸紡鍝嶅簲涓虹┖")
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

```
