# -*- coding: utf-8 -*-
"""LLM 调用日志。"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.drama.models import DramaLlmCallLog
from apps.drama.services.llm_call_context import (
    llm_call_scope,
    set_injection_manifest,
)
from apps.drama.services.llm_call_log_service import LlmCallLogService
from apps.drama.tests.helpers import create_project, create_user


class LlmCallLogServiceTests(TestCase):
    def test_record_persists_prompt_and_response(self):
        user = create_user("log-tester")
        project = create_project(user)
        with llm_call_scope(
            project_id=str(project.id),
            role="drama.topic-director",
            purpose=DramaLlmCallLog.Purpose.ARTIFACT_GENERATION,
            actor=user.username,
        ):
            log = LlmCallLogService.record(
                system_prompt="sys",
                user_prompt="user",
                model_name="test-model",
                base_url="https://example.com/v1",
                status=DramaLlmCallLog.Status.SUCCESS,
                latency_ms=120,
                response_json={
                    "id": "req-1",
                    "choices": [{"message": {"content": '{"ok": true}'}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                },
            )
        self.assertIsNotNone(log)
        assert log is not None
        self.assertEqual(log.project_id, project.id)
        self.assertEqual(log.role, "drama.topic-director")
        self.assertEqual(log.response_text, '{"ok": true}')
        self.assertEqual(log.total_tokens, 15)
        summary = LlmCallLogService.serialize_summary(log)
        self.assertEqual(summary["project_title"], project.title)
        self.assertEqual(summary["role_label"], "选题定调官")
        self.assertIsNone(summary.get("job_status"))

    def test_record_persists_cached_prompt_tokens(self):
        user = create_user("log-cache")
        project = create_project(user)
        with llm_call_scope(
            project_id=str(project.id),
            role="drama.topic-director",
            purpose=DramaLlmCallLog.Purpose.ARTIFACT_GENERATION,
            actor=user.username,
        ):
            log = LlmCallLogService.record(
                system_prompt="sys",
                user_prompt="user",
                model_name="test-model",
                base_url="https://example.com/v1",
                status=DramaLlmCallLog.Status.SUCCESS,
                latency_ms=10,
                response_json={
                    "choices": [{"message": {"content": "{}"}}],
                    "usage": {
                        "prompt_tokens": 1000,
                        "completion_tokens": 20,
                        "total_tokens": 1020,
                        "prompt_tokens_details": {"cached_tokens": 800},
                    },
                },
            )
        self.assertIsNotNone(log)
        assert log is not None
        self.assertEqual(log.prompt_tokens, 1000)
        self.assertEqual(log.cached_prompt_tokens, 800)

    def test_record_persists_injection_manifest_from_context(self):
        user = create_user("log-manifest")
        project = create_project(user)
        manifest = {
            "version": 1,
            "agent_id": "drama.topic-director",
            "system_chars": 12,
            "layers": {"skill": {"chars": 10, "truncated": False}},
        }
        with llm_call_scope(
            project_id=str(project.id),
            role="drama.topic-director",
            purpose=DramaLlmCallLog.Purpose.ARTIFACT_GENERATION,
            actor=user.username,
        ):
            set_injection_manifest(manifest)
            log = LlmCallLogService.record(
                system_prompt="sys",
                user_prompt="user",
                model_name="test-model",
                base_url="https://example.com/v1",
                status=DramaLlmCallLog.Status.SUCCESS,
                latency_ms=1,
                response_text="{}",
            )
        self.assertIsNotNone(log)
        assert log is not None
        self.assertEqual(log.injection_manifest["system_chars"], 12)
        detail = LlmCallLogService.serialize_detail(log)
        self.assertEqual(detail["injection_manifest"]["agent_id"], "drama.topic-director")
        self.assertEqual(detail["injection_system_chars"], 12)
        self.assertIs(detail["injection_truncated"], False)
    def test_record_keeps_long_raw_prompts_without_soft_truncate(self):
        """三栏原文不做 20 万软截断；完整落库便于排障。"""
        user = create_user("log-long")
        project = create_project(user)
        long_system = "S" * 250_000
        long_user = "U" * 250_000
        long_resp = "R" * 250_000
        with llm_call_scope(
            project_id=str(project.id),
            role="drama.script-scorer",
            purpose=DramaLlmCallLog.Purpose.QUALITY_SCORING,
            actor=user.username,
        ):
            log = LlmCallLogService.record(
                system_prompt=long_system,
                user_prompt=long_user,
                model_name="test-model",
                base_url="https://example.com/v1",
                status=DramaLlmCallLog.Status.SUCCESS,
                latency_ms=10,
                response_text=long_resp,
            )
        self.assertIsNotNone(log)
        assert log is not None
        self.assertEqual(len(log.system_prompt), 250_000)
        self.assertEqual(len(log.user_prompt), 250_000)
        self.assertEqual(len(log.response_text), 250_000)
        self.assertNotIn("已截断", log.system_prompt)
        self.assertNotIn("已截断", log.response_text)

    @patch("apps.drama.services.llm_provider.requests.post")
    def test_llm_provider_writes_log_on_success(self, mock_post):
        user = create_user("provider-log")
        project = create_project(user)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = [
            b'data: {"choices":[{"delta":{"content":"{\\"ok\\":true}"}}]}',
            b"data: [DONE]",
        ]
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        mock_post.return_value = mock_resp
        with patch("apps.drama.services.llm_provider.LlmConfigService.resolve") as resolve:
            resolve.return_value = MagicMock(
                enabled=True,
                base_url="https://example.com/v1",
                api_key="k",
                model="m",
                temperature=0.7,
                max_tokens=100,
            )
            with llm_call_scope(project_id=str(project.id), role="drama.writer"):
                from apps.drama.services.llm_provider import LlmProvider

                LlmProvider.chat_completion(system_prompt="s", user_prompt="u", json_mode=False)
        self.assertEqual(DramaLlmCallLog.objects.filter(project=project).count(), 1)

    def test_volces_skips_json_object_response_format(self):
        from apps.drama.services.llm_provider import LlmProvider

        self.assertFalse(
            LlmProvider._supports_json_object_format(
                "https://ark.cn-beijing.volces.com/api/v3"
            )
        )
        self.assertTrue(LlmProvider._supports_json_object_format("https://api.deepseek.com"))

    @patch("apps.drama.services.llm_provider.requests.post")
    def test_retries_without_response_format_when_unsupported(self, mock_post):
        bad = MagicMock()
        bad.status_code = 400
        bad.text = (
            '{"error":{"code":"InvalidParameter","message":'
            '"json_object is not supported by this model","param":"response_format.type"}}'
        )
        bad.__enter__.return_value = bad
        bad.__exit__.return_value = False

        good = MagicMock()
        good.status_code = 200
        good.iter_lines.return_value = [
            b'data: {"choices":[{"delta":{"content":"{}"}}]}',
            b"data: [DONE]",
        ]
        good.__enter__.return_value = good
        good.__exit__.return_value = False
        mock_post.side_effect = [bad, good]
        with patch("apps.drama.services.llm_provider.LlmConfigService.resolve") as resolve:
            resolve.return_value = MagicMock(
                enabled=True,
                base_url="https://api.openai.com/v1",
                api_key="k",
                model="m",
                temperature=0.7,
                max_tokens=100,
            )
            from apps.drama.services.llm_provider import LlmProvider

            result = LlmProvider.chat_completion(system_prompt="s", user_prompt="u", json_mode=True)
        self.assertEqual(mock_post.call_count, 2)
        first_body = mock_post.call_args_list[0].kwargs["json"]
        second_body = mock_post.call_args_list[1].kwargs["json"]
        self.assertIn("response_format", first_body)
        self.assertTrue(first_body.get("stream"))
        self.assertNotIn("response_format", second_body)
        self.assertIn("choices", result)
        self.assertEqual(result["choices"][0]["message"]["content"], "{}")
