# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
import requests

from apps.common.user_messages import humanize_llm_request_error
from apps.skill.llm.chat import LlmService, LlmServiceError
from apps.skill.llm.volcengine_chat import (
    http_error_is_model_not_found,
    is_volcano_endpoint_id,
    resolve_volcano_chat_model,
)


class VolcanoChatModelTests(SimpleTestCase):
    def test_is_ep(self):
        self.assertTrue(is_volcano_endpoint_id("ep-20260613155155-flkvt"))
        self.assertFalse(is_volcano_endpoint_id("deepseek-v4-pro"))

    @override_settings(VOLCANO_EP_DEEPSEEK_V4_PRO="ep-pro-test")
    def test_resolve_model_id_to_ep_via_env(self):
        resolved = resolve_volcano_chat_model(
            model="deepseek-v4-pro",
            catalog_preset_key="ark-deepseek-v4-pro",
            volcano_key_type="payg",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
        )
        self.assertEqual(resolved, "ep-pro-test")

    def test_coding_plan_keeps_model_id(self):
        resolved = resolve_volcano_chat_model(
            model="deepseek-v4-flash",
            catalog_preset_key="ark-deepseek-v4-flash",
            volcano_key_type="coding_plan",
            base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
        )
        self.assertEqual(resolved, "deepseek-v4-flash")

    def test_model_not_found_detected(self):
        resp = MagicMock(
            status_code=404,
            text='{"error":{"code":"InvalidEndpointOrModel.NotFound","message":"does not exist"}}',
        )
        exc = requests.HTTPError(response=resp)
        self.assertTrue(http_error_is_model_not_found(exc))

    def test_payg_404_hint_prefers_ep(self):
        msg = humanize_llm_request_error(
            requests.HTTPError(response=MagicMock(status_code=404, text="InvalidEndpointOrModel.NotFound")),
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model="doubao-seed-2.0-lite",
        )
        self.assertIn("ep-", msg)
        self.assertNotIn("最常见原因：Key 来自 Coding Plan", msg)

    @patch("apps.skill.llm.chat.LlmUsageService.record")
    @patch("apps.skill.llm.chat.LlmService._post_chat_completion")
    def test_no_base_url_alternate_on_model_not_found(self, mock_post, _record):
        not_found = requests.HTTPError(
            response=MagicMock(
                status_code=404,
                text='{"error":{"code":"InvalidEndpointOrModel.NotFound"}}',
            )
        )
        mock_post.side_effect = not_found
        cfg = {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "doubao-seed-2.0-lite",
            "api_key": "k",
        }
        body = {"model": "doubao-seed-2.0-lite", "messages": []}
        with self.assertRaises(LlmServiceError):
            LlmService._post_with_volcano_fallback(cfg=cfg, body=body, json_mode=False)
        self.assertEqual(mock_post.call_count, 1)
