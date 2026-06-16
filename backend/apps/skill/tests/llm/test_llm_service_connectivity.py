# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
import requests

from apps.common.user_messages import humanize_llm_request_error, volcano_alternate_base_url
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
    @override_settings(LLM_REQUEST_RETRIES=1)
    @patch.object(LlmService, "_request_timeout", return_value=(1, 1))
    @patch.object(LlmUsageService, "record")
    @patch.object(LlmService, "_post_chat_completion")
    @patch.object(LlmService, "_config")
    def test_chat_completion_retries_timeout(self, mock_config, mock_post, _record, _timeout):
        mock_config.return_value = {
            "api_key": "test-key",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "deepseek-v4-flash",
            "provider_name": "DeepSeek V4 Flash（火山）",
            "temperature": 0.6,
            "max_tokens": 16,
        }
        mock_post.side_effect = [
            requests.ReadTimeout("handshake timed out"),
            ("OK", {"total_tokens": 5}),
        ]

        result = LlmService._chat_completion(
            system_prompt="sys",
            user_prompt="user",
            temperature=None,
            max_tokens=16,
            provider_id="prov-1",
            json_mode=True,
        )

        self.assertEqual(result, "OK")
        self.assertEqual(mock_post.call_count, 2)

    @override_settings(LLM_REQUEST_RETRIES=1)
    @patch.object(LlmService, "_request_timeout", return_value=(1, 1))
    @patch.object(LlmUsageService, "record")
    @patch.object(LlmService, "_post_chat_completion")
    @patch.object(LlmService, "_config")
    def test_chat_completion_retries_http_500_without_thinking(self, mock_config, mock_post, _record, _timeout):
        mock_config.return_value = {
            "api_key": "test-key",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "deepseek-v4-flash",
            "provider_name": "DeepSeek V4 Flash（火山）",
            "temperature": 0.6,
            "max_tokens": 16,
        }
        resp = MagicMock()
        resp.status_code = 500
        resp.text = '{"error":{"message":"internal server error"}}'
        http_exc = requests.HTTPError(response=resp)
        http_exc.response = resp
        mock_post.side_effect = [
            http_exc,
            ("OK", {"total_tokens": 5}),
        ]

        result = LlmService._chat_completion(
            system_prompt="sys",
            user_prompt="user",
            temperature=None,
            max_tokens=16,
            provider_id="prov-1",
            json_mode=True,
        )

        self.assertEqual(result, "OK")
        self.assertEqual(mock_post.call_count, 2)
        first_body = mock_post.call_args_list[0].kwargs["body"]
        second_body = mock_post.call_args_list[1].kwargs["body"]
        self.assertEqual(first_body.get("thinking"), {"type": "disabled"})
        self.assertNotIn("thinking", second_body)

    def test_http_error_logs_redacted_response_body(self):
        resp = MagicMock()
        resp.status_code = 500
        resp.text = (
            '{"error":{"message":"internal server error",'
            '"debug":"Bearer secret-token api_key=secret-key"}}'
        )
        http_exc = requests.HTTPError(response=resp)
        http_exc.response = resp

        with self.assertLogs("apps.skill.llm.chat", level="WARNING") as logs:
            with self.assertRaises(LlmServiceError):
                LlmService._raise_http_error(
                    http_exc,
                    {
                        "provider_name": "DeepSeek V4 Flash（火山）",
                        "model": "ep-test",
                        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                    },
                )

        merged = "\n".join(logs.output)
        self.assertIn("status=500", merged)
        self.assertIn("internal server error", merged)
        self.assertIn("Bearer ***", merged)
        self.assertIn("api_key=***", merged)
        self.assertNotIn("secret-token", merged)
        self.assertNotIn("secret-key", merged)

    def test_proxy_error_message_is_actionable(self):
        exc = requests.exceptions.ProxyError("Unable to connect to proxy")

        msg = humanize_llm_request_error(
            exc,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model="deepseek-v4-pro",
        )

        self.assertIn("代理", msg)
        self.assertIn("ark.cn-beijing.volces.com", msg)

    @override_settings(LLM_REQUEST_RETRIES=0)
    @patch.object(LlmService, "_request_timeout", return_value=(1, 1))
    @patch.object(LlmUsageService, "record")
    @patch.object(LlmService, "_post_chat_completion")
    @patch.object(LlmService, "_config")
    def test_connection_failure_log_does_not_emit_none_traceback(
        self,
        mock_config,
        mock_post,
        _record,
        _timeout,
    ):
        mock_config.return_value = {
            "api_key": "test-key",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "deepseek-v4-pro",
            "provider_name": "DeepSeek V4 Pro（火山）",
            "temperature": 0.6,
            "max_tokens": 16,
        }
        mock_post.side_effect = requests.exceptions.ProxyError("Unable to connect to proxy")

        with self.assertLogs("apps.skill.llm.chat", level="ERROR") as logs:
            with self.assertRaises(LlmServiceError):
                LlmService._chat_completion(
                    system_prompt="sys",
                    user_prompt="user",
                    temperature=None,
                    max_tokens=16,
                    provider_id="prov-1",
                    json_mode=True,
                )

        merged = "\n".join(logs.output)
        self.assertIn("LLM 请求失败", merged)
        self.assertIn("Unable to connect to proxy", merged)
        self.assertNotIn("NoneType: None", merged)

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
        http_exc.response.text = '{"error":{"code":"NotFound","message":"route not found"}}'

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
