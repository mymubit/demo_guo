# -*- coding: utf-8 -*-
"""P5-W1：多 Key 模型 / 轮询 / REST。"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from apps.drama.models import (
    DramaLlmProvider,
    V3CommandRun,
    V3FailoverAttempt,
    V3LlmProviderKey,
    V3Project,
    V3RoleModelMapping,
)
from apps.drama.orchestrator.llm_router import chat_with_failover
from apps.drama.orchestrator.provider_keys import iter_api_keys, iter_provider_key_slots
from apps.drama.services.llm_provider import LlmProviderError
from apps.drama.services.secret_crypto import decrypt_secret, encrypt_secret
from apps.drama.tests.helpers import SKILLS_ROOT


def _make_provider(**overrides) -> DramaLlmProvider:
    data = {
        "name": "provider",
        "base_url": "https://llm.example/v1",
        "model_name": "gpt-test",
        "api_key_encrypted": encrypt_secret("sk-primary"),
        "temperature": 0.7,
        "max_tokens": 4096,
        "is_enabled": True,
        "is_active": True,
    }
    data.update(overrides)
    return DramaLlmProvider.objects.create(**data)


class ProviderKeysHelperTests(TestCase):
    def test_iter_api_keys_primary_then_enabled_extras_ordered(self) -> None:
        provider = _make_provider()
        V3LlmProviderKey.objects.create(
            provider=provider,
            label="备用B",
            api_key_encrypted=encrypt_secret("sk-b"),
            sort_order=20,
            is_enabled=True,
        )
        V3LlmProviderKey.objects.create(
            provider=provider,
            label="备用A",
            api_key_encrypted=encrypt_secret("sk-a"),
            sort_order=10,
            is_enabled=True,
        )
        V3LlmProviderKey.objects.create(
            provider=provider,
            label="停用",
            api_key_encrypted=encrypt_secret("sk-off"),
            sort_order=5,
            is_enabled=False,
        )

        self.assertEqual(iter_api_keys(provider), ["sk-primary", "sk-a", "sk-b"])
        slots = iter_provider_key_slots(provider)
        self.assertEqual([s.label for s in slots], ["主密钥", "备用A", "备用B"])
        self.assertTrue(slots[0].is_primary)
        self.assertFalse(slots[1].is_primary)

    def test_iter_api_keys_skips_empty_primary(self) -> None:
        provider = _make_provider(api_key_encrypted="")
        V3LlmProviderKey.objects.create(
            provider=provider,
            label="only",
            api_key_encrypted=encrypt_secret("sk-only"),
            sort_order=1,
            is_enabled=True,
        )
        self.assertEqual(iter_api_keys(provider), ["sk-only"])


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class MultiKeyRouterTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user("mk-router", password="x")
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

    def test_rotates_keys_within_provider_before_backup(self) -> None:
        p1 = _make_provider(name="P1", api_key_encrypted=encrypt_secret("sk-p1-a"))
        V3LlmProviderKey.objects.create(
            provider=p1,
            label="P1-extra",
            api_key_encrypted=encrypt_secret("sk-p1-b"),
            sort_order=1,
            is_enabled=True,
        )
        p2 = _make_provider(
            name="P2",
            is_active=False,
            api_key_encrypted=encrypt_secret("sk-p2"),
            base_url="https://p2.example/v1",
        )
        V3RoleModelMapping.objects.create(
            role_key="drama-script-writer",
            provider=p1,
            backup_provider_ids=[str(p2.id)],
        )
        fake_resp = {"choices": [{"message": {"content": '{"ok": true}'}}]}
        seen_keys: list[str] = []

        def chat_fn(*, system_prompt, user_prompt, json_mode=True, config=None, **_kwargs):
            key = config.api_key if config else ""
            seen_keys.append(key)
            if key != "sk-p1-b":
                raise LlmProviderError("LLM HTTP 429: rate limited")
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
        self.assertEqual(seen_keys, ["sk-p1-a", "sk-p1-b"])
        attempts = list(V3FailoverAttempt.objects.order_by("created_at"))
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0].status, V3FailoverAttempt.Status.FAILED_SWITCHABLE)
        self.assertEqual(attempts[0].provider_id, p1.id)
        self.assertEqual(attempts[0].error_code, "http_429")
        self.assertIn("主密钥", attempts[0].error_message)
        self.assertNotIn("sk-p1-a", attempts[0].error_message)
        self.assertEqual(attempts[1].status, V3FailoverAttempt.Status.SUCCEEDED)
        self.assertEqual(attempts[1].provider_id, p1.id)
        self.assertEqual(V3FailoverAttempt.objects.filter(provider=p2).count(), 0)

    def test_all_keys_fail_then_next_provider(self) -> None:
        p1 = _make_provider(name="P1", api_key_encrypted=encrypt_secret("sk-p1"))
        V3LlmProviderKey.objects.create(
            provider=p1,
            label="extra",
            api_key_encrypted=encrypt_secret("sk-extra"),
            sort_order=1,
            is_enabled=True,
        )
        p2 = _make_provider(
            name="P2",
            is_active=False,
            api_key_encrypted=encrypt_secret("sk-p2"),
            base_url="https://p2.example/v1",
        )
        V3RoleModelMapping.objects.create(
            role_key="drama-script-writer",
            provider=p1,
            backup_provider_ids=[str(p2.id)],
        )
        fake_resp = {"choices": [{"message": {"content": '{"ok": true}'}}]}
        seen_keys: list[str] = []

        def chat_fn(*, system_prompt, user_prompt, json_mode=True, config=None, **_kwargs):
            key = config.api_key if config else ""
            seen_keys.append(key)
            if key == "sk-p2":
                return fake_resp
            raise LlmProviderError("LLM HTTP 503: unavailable")

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
        self.assertEqual(seen_keys, ["sk-p1", "sk-extra", "sk-p2"])
        self.assertEqual(V3FailoverAttempt.objects.filter(provider=p1).count(), 2)
        self.assertEqual(
            V3FailoverAttempt.objects.filter(
                provider=p2, status=V3FailoverAttempt.Status.SUCCEEDED
            ).count(),
            1,
        )


class V3ProviderKeysApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="keys_api", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.provider = _make_provider(name="api-provider")

    def _keys_url(self, provider_id=None) -> str:
        pid = provider_id or self.provider.id
        return f"/api/v3/models/providers/{pid}/keys/"

    def test_create_list_never_returns_plaintext(self) -> None:
        resp = self.client.post(
            self._keys_url(),
            {"label": "备用1", "api_key": "sk-extra-secret", "sort_order": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        created = resp.json()["data"]
        self.assertNotIn("api_key", created)
        self.assertTrue(created["api_key_set"])
        self.assertEqual(created["label"], "备用1")
        self.assertEqual(created["sort_order"], 1)
        self.assertTrue(created["is_enabled"])

        listed = self.client.get(self._keys_url())
        self.assertEqual(listed.status_code, 200)
        items = listed.json()["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertNotIn("api_key", items[0])
        self.assertTrue(items[0]["api_key_set"])
        obj = V3LlmProviderKey.objects.get(pk=created["id"])
        self.assertEqual(decrypt_secret(obj.api_key_encrypted), "sk-extra-secret")

    def test_patch_and_delete(self) -> None:
        created = self.client.post(
            self._keys_url(),
            {"label": "k1", "api_key": "sk-old", "sort_order": 2},
            format="json",
        ).json()["data"]
        key_id = created["id"]
        before = V3LlmProviderKey.objects.get(pk=key_id).api_key_encrypted

        patch = self.client.patch(
            f"{self._keys_url()}{key_id}/",
            {"label": "k1-renamed", "api_key": "", "is_enabled": False},
            format="json",
        )
        self.assertEqual(patch.status_code, 200)
        data = patch.json()["data"]
        self.assertEqual(data["label"], "k1-renamed")
        self.assertFalse(data["is_enabled"])
        self.assertTrue(data["api_key_set"])
        self.assertNotIn("api_key", data)
        self.assertEqual(
            V3LlmProviderKey.objects.get(pk=key_id).api_key_encrypted, before
        )

        patch_key = self.client.patch(
            f"{self._keys_url()}{key_id}/",
            {"api_key": "sk-new"},
            format="json",
        )
        self.assertEqual(patch_key.status_code, 200)
        self.assertEqual(
            decrypt_secret(V3LlmProviderKey.objects.get(pk=key_id).api_key_encrypted),
            "sk-new",
        )

        deleted = self.client.delete(f"{self._keys_url()}{key_id}/")
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(V3LlmProviderKey.objects.filter(pk=key_id).exists())

    def test_unauthenticated_rejected(self) -> None:
        self.client.force_authenticate(user=None)
        resp = self.client.get(self._keys_url())
        self.assertIn(resp.status_code, (401, 403))
