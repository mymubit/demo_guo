# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.common.user_messages import volcano_alternate_base_url
from apps.skill.llm.chat import LlmService, LlmServiceError
from apps.skill.llm.usage_log import LlmUsageService


class VolcanoAlternateBaseUrlTests(SimpleTestCase):
    def test_payg_to_coding(self):
        self.assertEqual(
            volcano_alternate_base_url("https://ark.cn-beijing.volces.com/api/v3"),
            "https://ark.cn-beijing.volces.com/api/coding/v3",
        )

    def test_coding_to_payg(self):
        self.assertEqual(
            volcano_alternate_base_url("https://ark.cn-beijing.volces.com/api/coding/v3"),
            "https://ark.cn-beijing.volces.com/api/v3",
        )


class LlmServiceConnectivityTests(SimpleTestCase):
    @patch.object(LlmUsageService, "record")
    @patch.object(LlmService, "_post_chat_completion")
    @patch.object(LlmService, "_config")
    def test_volcano_404_retries_alternate_base_url(self, mock_config, mock_post, mock_record):
        mock_config.return_value = {
            "api_key": "test-key",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "deepseek-v4-flash",
            "provider_name": "DeepSeek V4 Flash（火山）",
            "temperature": 0.6,
            "max_tokens": 16,
        }

        http_exc = MagicMock()
        http_exc.response.status_code = 404
        http_exc.response.text = '{"error":{"code":"InvalidEndpointOrModel.NotFound"}}'

        import requests

        first = requests.HTTPError(response=http_exc.response)
        first.response = http_exc.response

        mock_post.side_effect = [first, ("OK", {"total_tokens": 5, "prompt_tokens": 3, "completion_tokens": 2})]

        result = LlmService.test_connectivity(provider_id="prov-1", auto_save=False)

        self.assertTrue(result["ok"])
        self.assertEqual(result["sample"], "OK")
        self.assertEqual(
            result["suggested_base_url"],
            "https://ark.cn-beijing.volces.com/api/coding/v3",
        )
        self.assertIn("Base URL", result["message"])
        self.assertEqual(mock_post.call_count, 2)

    @patch.object(LlmUsageService, "record")
    @patch.object(LlmService, "_post_chat_completion")
    @patch.object(LlmService, "_config")
    def test_volcano_404_both_fail_raises_original(self, mock_config, mock_post, mock_record):
        mock_config.return_value = {
            "api_key": "test-key",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "deepseek-v4-flash",
            "provider_name": "DeepSeek V4 Flash（火山）",
            "temperature": 0.6,
            "max_tokens": 16,
        }

        import requests

        resp = MagicMock()
        resp.status_code = 404
        resp.text = '{"error":{"code":"InvalidEndpointOrModel.NotFound"}}'
        http_exc = requests.HTTPError(response=resp)
        http_exc.response = resp

        def _raise_http(*args, **kwargs):
            raise http_exc

        mock_post.side_effect = _raise_http

        with self.assertRaises(LlmServiceError) as ctx:
            LlmService.test_connectivity(provider_id="prov-1", auto_save=False)

        self.assertIn("404", str(ctx.exception))
