# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
import requests

from apps.skill.llm.chat import LlmService


class LlmJsonFallbackTests(SimpleTestCase):
    def test_json_object_unsupported_detected(self):
        resp = MagicMock()
        resp.status_code = 400
        resp.text = '{"error":{"message":"json_object is not supported by this model"}}'
        exc = requests.HTTPError(response=resp)
        self.assertTrue(LlmService._json_object_unsupported(exc))

    @patch("apps.skill.llm.chat.LlmUsageService.record")
    @patch("apps.skill.llm.chat.LlmService._post_chat_completion")
    def test_post_with_volcano_fallback_retries_without_json_format(self, mock_post, _record):
        json_exc = requests.HTTPError(response=MagicMock(status_code=400, text="json_object is not supported"))
        mock_post.side_effect = [
            json_exc,
            ('{"ok": true}', {"total_tokens": 10}),
        ]
        cfg = {"base_url": "https://ark.cn-beijing.volces.com/api/v3", "model": "deepseek-v4-pro", "api_key": "k"}
        body = {
            "model": "deepseek-v4-pro",
            "messages": [],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
        }
        content, detected = LlmService._post_with_volcano_fallback(cfg=cfg, body=body, json_mode=True)
        self.assertEqual(content, '{"ok": true}')
        self.assertIsNone(detected)
        self.assertEqual(mock_post.call_count, 2)
        fallback_body = mock_post.call_args_list[1].kwargs["body"]
        self.assertNotIn("response_format", fallback_body)

    def test_volcano_ep_json_mode_disables_thinking(self):
        cfg = {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "ep-20260613155155-flkvt",
            "vendor": "volcengine",
            "catalog_preset_key": "deepseek-v4-pro",
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        body = LlmService._build_chat_body(
            cfg=cfg,
            system_prompt="sys",
            user_prompt="user",
            temperature=None,
            max_tokens=None,
            json_mode=True,
        )
        self.assertEqual(body["thinking"], {"type": "disabled"})
        self.assertNotIn("response_format", body)

    @patch("apps.skill.llm.chat.LlmUsageService.record")
    @patch("apps.skill.llm.chat.LlmService._post_chat_completion")
    def test_json_object_retry_with_thinking_disabled_before_strip(self, mock_post, _record):
        json_exc = requests.HTTPError(response=MagicMock(status_code=400, text="json_object is not supported"))
        mock_post.side_effect = [
            json_exc,
            ('{"ok": true}', {"total_tokens": 10}),
        ]
        cfg = {"base_url": "https://ark.cn-beijing.volces.com/api/v3", "model": "deepseek-v4-pro", "api_key": "k"}
        body = {
            "model": "deepseek-v4-pro",
            "messages": [],
            "response_format": {"type": "json_object"},
        }
        content, _ = LlmService._post_with_volcano_fallback(cfg=cfg, body=body, json_mode=True)
        self.assertEqual(content, '{"ok": true}')
        self.assertEqual(mock_post.call_count, 2)
        retry_body = mock_post.call_args_list[1].kwargs["body"]
        self.assertEqual(retry_body.get("thinking"), {"type": "disabled"})
        self.assertEqual(retry_body.get("response_format"), {"type": "json_object"})
