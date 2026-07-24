# -*- coding: utf-8 -*-
"""W5 Task 5：test_model_provider 同步试连 + 角色映射优先于 active。"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase

from apps.drama.models import (
    DramaLlmCallLog,
    DramaLlmProvider,
    V3CommandRun,
    V3FailoverAttempt,
    V3RoleModelMapping,
)
from apps.drama.orchestrator import dispatch_command
from apps.drama.services.llm_config_service import LlmConfigService, ResolvedLlmConfig
from apps.drama.services.secret_crypto import encrypt_secret
from apps.drama.skills_bridge.executor import _default_llm_call


def _make_provider(**overrides) -> DramaLlmProvider:
    data = {
        "name": "probe-provider",
        "base_url": "https://llm.example/v1",
        "model_name": "gpt-probe",
        "api_key_encrypted": encrypt_secret("sk-probe-secret"),
        "temperature": 0.5,
        "max_tokens": 2048,
        "is_enabled": True,
        "is_active": False,
    }
    data.update(overrides)
    return DramaLlmProvider.objects.create(**data)


class V3ProviderTestCommandTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="provider_test", password="pass12345"
        )
        self.provider = _make_provider(is_active=True)

    @patch("apps.drama.orchestrator.provider_test.requests.get")
    def test_test_model_provider_sync_success_writes_log(self, mock_get) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"data":[]}'
        mock_get.return_value = mock_resp

        run = dispatch_command(
            owner=self.user,
            command_type="test_model_provider",
            payload={"provider_id": str(self.provider.id)},
        )
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        self.assertTrue(run.result_payload.get("ok"))
        self.assertEqual(run.result_payload.get("status_code"), 200)
        self.assertIn("连通", run.result_payload.get("message", ""))

        mock_get.assert_called_once()
        url = mock_get.call_args.args[0]
        self.assertTrue(url.endswith("/models"))
        headers = mock_get.call_args.kwargs.get("headers") or {}
        self.assertIn("Bearer", headers.get("Authorization", ""))

        log = DramaLlmCallLog.objects.filter(
            purpose=DramaLlmCallLog.Purpose.CONNECTIVITY_TEST
        ).latest("created_at")
        self.assertEqual(log.status, DramaLlmCallLog.Status.SUCCESS)
        self.assertEqual(log.model_name, "gpt-probe")
        self.assertEqual(str(log.v3_command_run_id), str(run.id))
        self.assertNotIn("sk-probe", (log.response_text or "") + (log.error_message or ""))
        # 试连直连指定 provider，不经主备链
        self.assertEqual(V3FailoverAttempt.objects.count(), 0)

    @patch("apps.drama.orchestrator.provider_test.requests.get")
    def test_test_model_provider_http_failure_is_failed_with_zh(self, mock_get) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "unauthorized"
        mock_get.return_value = mock_resp

        run = dispatch_command(
            owner=self.user,
            command_type="test_model_provider",
            payload={"provider_id": str(self.provider.id)},
        )
        self.assertEqual(run.status, V3CommandRun.Status.FAILED)
        self.assertIn("连通失败", run.error_message)

        log = DramaLlmCallLog.objects.filter(
            purpose=DramaLlmCallLog.Purpose.CONNECTIVITY_TEST
        ).latest("created_at")
        self.assertEqual(log.status, DramaLlmCallLog.Status.ERROR)
        self.assertEqual(str(log.v3_command_run_id), str(run.id))

    def test_test_model_provider_missing_provider_id_fails(self) -> None:
        run = dispatch_command(
            owner=self.user,
            command_type="test_model_provider",
            payload={},
        )
        self.assertEqual(run.status, V3CommandRun.Status.FAILED)
        self.assertIn("provider", run.error_message.lower() + run.error_message)

    @patch("apps.drama.orchestrator.provider_test.requests.get")
    def test_test_model_provider_not_stub(self, mock_get) -> None:
        """不再返回 unsupported stub。"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"
        mock_get.return_value = mock_resp
        run = dispatch_command(
            owner=self.user,
            command_type="test_model_provider",
            payload={"provider_id": str(self.provider.id)},
        )
        self.assertNotEqual(run.status, V3CommandRun.Status.UNSUPPORTED)
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)


class V3ProviderTestRestTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="provider_rest", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.provider = _make_provider(is_active=True)

    @patch("apps.drama.orchestrator.provider_test.requests.get")
    def test_dispatcher_connectivity_log_visible_on_run_detail(self, mock_get) -> None:
        """试连经 dispatcher 后，GET logs/runs/{id}/ 可见 CONNECTIVITY_TEST call。"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"data":[]}'
        mock_get.return_value = mock_resp

        run = dispatch_command(
            owner=self.user,
            command_type="test_model_provider",
            payload={"provider_id": str(self.provider.id)},
        )
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)

        resp = self.client.get(f"/api/v3/logs/runs/{run.id}/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["command_type"], "test_model_provider")
        self.assertEqual(len(data["calls"]), 1)
        call = data["calls"][0]
        self.assertEqual(call["purpose"], DramaLlmCallLog.Purpose.CONNECTIVITY_TEST)
        self.assertEqual(call["v3_command_run_id"], str(run.id))

    @patch("apps.drama.orchestrator.provider_test.requests.get")
    def test_rest_provider_test_endpoint(self, mock_get) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"
        mock_get.return_value = mock_resp

        resp = self.client.post(
            f"/api/v3/models/providers/{self.provider.id}/test/",
            {},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertTrue(data["ok"])
        self.assertNotIn("api_key", data)
        self.assertTrue(
            DramaLlmCallLog.objects.filter(
                purpose=DramaLlmCallLog.Purpose.CONNECTIVITY_TEST
            ).exists()
        )


class V3RoleMappingResolveTests(TestCase):
    def setUp(self) -> None:
        self.active = _make_provider(
            name="active",
            base_url="https://active.example/v1",
            model_name="model-active",
            api_key_encrypted=encrypt_secret("sk-active"),
            is_active=True,
            temperature=0.7,
            max_tokens=4096,
        )
        self.mapped = _make_provider(
            name="mapped",
            base_url="https://mapped.example/v1",
            model_name="model-mapped",
            api_key_encrypted=encrypt_secret("sk-mapped"),
            is_active=False,
            temperature=0.1,
            max_tokens=512,
        )

    def test_resolve_for_role_uses_mapping_over_active(self) -> None:
        V3RoleModelMapping.objects.create(
            role_key="drama-topic-director",
            provider=self.mapped,
            temperature=0.2,
            max_tokens=1024,
        )
        cfg = LlmConfigService.resolve_for_role("drama-topic-director")
        self.assertEqual(cfg.base_url, "https://mapped.example/v1")
        self.assertEqual(cfg.model, "model-mapped")
        self.assertEqual(cfg.api_key, "sk-mapped")
        self.assertEqual(cfg.temperature, 0.2)
        self.assertEqual(cfg.max_tokens, 1024)
        self.assertEqual(cfg.source, "db_role_mapping")

    def test_resolve_for_role_falls_back_to_active(self) -> None:
        cfg = LlmConfigService.resolve_for_role("drama-script-writer")
        active_cfg = LlmConfigService.resolve()
        self.assertEqual(cfg.base_url, active_cfg.base_url)
        self.assertEqual(cfg.model, active_cfg.model)
        self.assertEqual(cfg.api_key, active_cfg.api_key)

    @patch("apps.drama.services.llm_provider.LlmProvider.chat_completion")
    def test_executor_default_llm_call_passes_mapped_config(self, mock_chat) -> None:
        V3RoleModelMapping.objects.create(
            role_key="drama-topic-director",
            provider=self.mapped,
        )
        mock_chat.return_value = {
            "choices": [{"message": {"content": '{"ok":true}'}}]
        }
        text = _default_llm_call("hello", role="drama-topic-director")
        self.assertEqual(text, '{"ok":true}')
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        cfg = kwargs.get("config")
        self.assertIsInstance(cfg, ResolvedLlmConfig)
        self.assertEqual(cfg.base_url, "https://mapped.example/v1")
        self.assertEqual(cfg.model, "model-mapped")
        self.assertEqual(cfg.api_key, "sk-mapped")
