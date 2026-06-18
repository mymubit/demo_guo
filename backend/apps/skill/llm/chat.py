# -*- coding: utf-8 -*-
"""OpenAI 兼容 Chat Completions — 配置来自 LlmProvider（多模型）。"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, Optional, Tuple

import requests
from django.conf import settings

from apps.common.user_messages import humanize_llm_request_error, humanize_user_message
from apps.skill.llm.providers import LlmProviderService
from apps.skill.llm.usage_log import LlmUsageService
from apps.skill.llm.volcengine_config import (
    infer_key_type_from_alternate_success,
    is_volcano_host,
    volcano_alternate_base_url,
)
from apps.skill.llm.volcengine_chat import http_error_is_model_not_found, is_volcano_endpoint_id

logger = logging.getLogger(__name__)


class LlmServiceError(Exception):
    pass


class LlmService:
    @staticmethod
    def _chat_completions_url(base_url: str) -> str:
        base = (base_url or "").strip().rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"

    @staticmethod
    def _is_volcano_base(base_url: str) -> bool:
        return is_volcano_host(base_url)

    @staticmethod
    def _request_timeout(json_mode: bool) -> Tuple[int, int]:
        connect = int(getattr(settings, "LLM_CONNECT_TIMEOUT", 30) or 30)
        if json_mode:
            read = int(getattr(settings, "LLM_READ_TIMEOUT_JSON", 600) or 600)
        else:
            read = int(getattr(settings, "LLM_READ_TIMEOUT_TEXT", 120) or 120)
        return connect, read

    @classmethod
    def is_enabled(cls) -> bool:
        if not getattr(settings, "FUSION_LLM_ENABLED", True):
            return False
        return LlmProviderService.global_enabled()

    @classmethod
    def _config(cls, provider_id: Optional[str] = None) -> Dict[str, Any]:
        provider = None
        if provider_id:
            provider = LlmProviderService.get_by_id(provider_id)
            if provider is None:
                raise LlmServiceError("指定的大模型配置不存在")
        return LlmProviderService.runtime_config(provider)

    @classmethod
    def _use_api_json_object(cls, cfg: Dict[str, Any], *, json_mode: bool) -> bool:
        """是否向 API 发送 response_format=json_object（火山 ep- 接入点不支持，走 Prompt JSON）。"""
        if not json_mode:
            return False
        model = str(cfg.get("model") or "")
        if cls._is_volcano_base(cfg.get("base_url") or "") and is_volcano_endpoint_id(model):
            return False
        return True

    @classmethod
    def _wants_thinking_disabled(cls, cfg: Dict[str, Any], *, json_mode: bool) -> bool:
        """JSON 结构化输出时关闭 thinking（火山 DeepSeek/Seed 官方要求）。"""
        if not json_mode:
            return False
        model_name = str(cfg.get("model") or "").lower()
        vendor = str(cfg.get("vendor") or "").lower()
        preset = str(cfg.get("catalog_preset_key") or "").lower()
        provider_name = str(cfg.get("provider_name") or "").lower()
        base_url = cfg.get("base_url") or ""
        if cls._is_volcano_base(base_url):
            return True
        tokens = ("deepseek", "seed")
        if any(token in text for text in (model_name, preset, provider_name) for token in tokens):
            return True
        return vendor in ("volcengine", "deepseek")

    @classmethod
    def _build_chat_body(
        cls,
        *,
        cfg: Dict[str, Any],
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        json_mode: bool,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "model": cfg["model"],
            "temperature": temperature if temperature is not None else cfg["temperature"],
            "max_tokens": max_tokens or cfg["max_tokens"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if cls._use_api_json_object(cfg, json_mode=json_mode):
            body["response_format"] = {"type": "json_object"}
        if cls._wants_thinking_disabled(cfg, json_mode=json_mode):
            body["thinking"] = {"type": "disabled"}
        return body

    @classmethod
    def _raise_http_error(cls, exc: requests.HTTPError, cfg: Dict[str, Any]) -> None:
        resp_body = ""
        try:
            if exc.response is not None:
                resp_body = (exc.response.text or "")[:500]
        except Exception:  # noqa: BLE001
            pass
        cls._log_http_error_response(exc, cfg, response_body=resp_body)
        raise LlmServiceError(
            humanize_llm_request_error(
                exc,
                base_url=cfg.get("base_url") or "",
                model=cfg.get("model") or "",
                response_body=resp_body,
            )
        ) from exc

    @staticmethod
    def _redact_response_body(text: str) -> str:
        body = str(text or "")
        body = re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer ***", body, flags=re.I)
        body = re.sub(r"(api[_-]?key|access[_-]?token|secret)\s*[:=]\s*['\"]?[^,'\"}\s]+", r"\1=***", body, flags=re.I)
        body = re.sub(r"\b(sk|ak)-[A-Za-z0-9_\-]{12,}\b", r"\1-***", body)
        return body[:1000]

    @classmethod
    def _log_http_error_response(
        cls,
        exc: requests.HTTPError,
        cfg: Dict[str, Any],
        *,
        response_body: str = "",
    ) -> None:
        resp = getattr(exc, "response", None)
        status_code = getattr(resp, "status_code", None)
        body = cls._redact_response_body(response_body)
        logger.warning(
            "LLM HTTP 错误 provider=%s model=%s status=%s base_url=%s response_body=%s",
            cfg.get("provider_name") or "",
            cfg.get("model") or "",
            status_code or "",
            cfg.get("base_url") or "",
            body or "<empty>",
        )

    @staticmethod
    def _record_failed_usage(cfg: Dict[str, Any]) -> None:
        LlmUsageService.record(cfg=cfg, usage={}, success=False)

    @classmethod
    def _json_object_unsupported(cls, exc: requests.HTTPError) -> bool:
        resp = exc.response
        if resp is None or resp.status_code != 400:
            return False
        text = (resp.text or "").lower()
        return "json_object" in text and "not supported" in text

    @staticmethod
    def _retryable_http_status(exc: Exception) -> Optional[int]:
        cause = getattr(exc, "__cause__", None)
        if isinstance(exc, requests.HTTPError):
            http_exc = exc
        elif isinstance(cause, requests.HTTPError):
            http_exc = cause
        else:
            return None
        resp = getattr(http_exc, "response", None)
        status_code = getattr(resp, "status_code", None)
        if status_code in {408, 409, 425, 429} or (isinstance(status_code, int) and status_code >= 500):
            return int(status_code)
        return None

    @classmethod
    def _post_chat_completion(
        cls,
        *,
        cfg: Dict[str, Any],
        body: Dict[str, Any],
        json_mode: bool,
    ) -> Tuple[str, Dict[str, Any]]:
        url = cls._chat_completions_url(cfg["base_url"])
        headers = {
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        }
        timeout = cls._request_timeout(json_mode)
        resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage") if isinstance(data, dict) else {}
        content = (data["choices"][0]["message"]["content"] or "").strip()
        return content, usage if isinstance(usage, dict) else {}

    @classmethod
    def _post_with_volcano_fallback(
        cls,
        *,
        cfg: Dict[str, Any],
        body: Dict[str, Any],
        json_mode: bool,
    ) -> Tuple[str, Optional[Dict[str, str]]]:
        """请求 Chat Completions；火山 404 时自动尝试 alternate Base URL。"""

        def _attempt(active_cfg: Dict[str, Any], active_body: Dict[str, Any], *, use_json_mode: bool) -> str:
            api_json = cls._use_api_json_object(active_cfg, json_mode=use_json_mode)
            try:
                content, usage = cls._post_chat_completion(
                    cfg=active_cfg, body=active_body, json_mode=use_json_mode
                )
                LlmUsageService.record(cfg=active_cfg, usage=usage, success=True)
                return content
            except requests.HTTPError as exc:
                if api_json and cls._json_object_unsupported(exc):
                    if active_body.get("thinking") != {"type": "disabled"}:
                        retry_body = dict(active_body)
                        retry_body["thinking"] = {"type": "disabled"}
                        retry_body.setdefault("response_format", {"type": "json_object"})
                        try:
                            content, usage = cls._post_chat_completion(
                                cfg=active_cfg, body=retry_body, json_mode=True
                            )
                            LlmUsageService.record(cfg=active_cfg, usage=usage, success=True)
                            return content
                        except requests.HTTPError as exc2:
                            if not cls._json_object_unsupported(exc2):
                                cls._raise_http_error(exc2, active_cfg)

                    logger.warning(
                        "模型 %s 的接入点不支持 Chat response_format=json_object"
                        "（火山部分 ep- 接入点仅支持 Prompt 约束 JSON）；"
                        "已降级为 Prompt JSON 解析。"
                        "建议改用 Model ID（如 deepseek-v4-flash）或开通支持结构化的接入点。",
                        active_cfg.get("model"),
                    )
                    fallback_body = dict(active_body)
                    fallback_body.pop("response_format", None)
                    for conn_try in range(1, 4):
                        try:
                            content, usage = cls._post_chat_completion(
                                cfg=active_cfg, body=fallback_body, json_mode=False
                            )
                            LlmUsageService.record(cfg=active_cfg, usage=usage, success=True)
                            return content
                        except requests.ConnectionError as conn_exc:
                            if conn_try >= 3:
                                raise conn_exc
                            logger.warning(
                                "LLM 连接被重置 provider=%s model=%s retry=%s/3",
                                active_cfg.get("provider_name"),
                                active_cfg.get("model"),
                                conn_try,
                            )
                            time.sleep(min(conn_try * 2, 6))
                status_code = cls._retryable_http_status(exc)
                if status_code and active_body.get("thinking") is not None:
                    retry_body = dict(active_body)
                    retry_body.pop("thinking", None)
                    logger.warning(
                        "LLM 服务端临时异常，尝试移除 thinking 参数重试 provider=%s status=%s",
                        active_cfg.get("provider_name"),
                        status_code,
                    )
                    try:
                        content, usage = cls._post_chat_completion(
                            cfg=active_cfg, body=retry_body, json_mode=use_json_mode
                        )
                        LlmUsageService.record(cfg=active_cfg, usage=usage, success=True)
                        return content
                    except requests.HTTPError:
                        pass
                cls._raise_http_error(exc, active_cfg)
            except (requests.Timeout, requests.ConnectionError):
                raise
            except requests.RequestException as exc:
                raise LlmServiceError(
                    humanize_llm_request_error(
                        exc,
                        base_url=active_cfg.get("base_url") or "",
                        model=active_cfg.get("model") or "",
                    )
                ) from exc
            raise LlmServiceError("大模型连接失败")  # pragma: no cover

        base_url = str(cfg.get("base_url") or "")
        try:
            return _attempt(cfg, body, use_json_mode=json_mode), None
        except LlmServiceError as first_exc:
            if not cls._is_volcano_base(base_url):
                raise
            resp = getattr(getattr(first_exc, "__cause__", None), "response", None)
            if getattr(resp, "status_code", None) != 404:
                raise
            if http_error_is_model_not_found(getattr(first_exc, "__cause__", None) or first_exc):
                raise

            alternate = volcano_alternate_base_url(base_url)
            alt_cfg = {**cfg, "base_url": alternate}
            try:
                sample = _attempt(alt_cfg, body, use_json_mode=json_mode)
            except LlmServiceError:
                raise first_exc from None

            key_type = infer_key_type_from_alternate_success(
                tried_base_url=base_url,
                success_base_url=alternate,
            )
            return sample, {
                "suggested_base_url": alternate,
                "previous_base_url": base_url,
                "volcano_key_type": key_type,
            }

    @classmethod
    def test_connectivity(
        cls,
        *,
        provider_id: Optional[str] = None,
        auto_save: bool = True,
    ) -> Dict[str, Any]:
        cfg = cls._config(provider_id)
        if not cfg["api_key"] or not cfg["base_url"]:
            raise LlmServiceError("LLM 配置不完整：请在后台添加并启用一个大模型")

        from apps.skill.llm.usage_log import llm_usage_scope
        from apps.skill.models import LlmUsageLog

        body = cls._build_chat_body(
            cfg=cfg,
            system_prompt="You are a connectivity test assistant.",
            user_prompt="Reply with exactly: OK",
            temperature=0,
            max_tokens=16,
            json_mode=False,
        )
        with llm_usage_scope(source_type=LlmUsageLog.SOURCE_TEST, source_key="connectivity"):
            sample, detected = cls._post_with_volcano_fallback(cfg=cfg, body=body, json_mode=False)

        result: Dict[str, Any] = {
            "ok": True,
            "sample": (sample or "")[:200],
            "provider_name": cfg.get("provider_name"),
            "model": cfg.get("model"),
            "model_configured": cfg.get("model_configured") or cfg.get("model"),
            "base_url": detected["suggested_base_url"] if detected else cfg.get("base_url"),
        }

        configured = cfg.get("model_configured") or cfg.get("model")
        resolved = cfg.get("model")
        if configured and resolved and configured != resolved:
            result["model_resolved_from"] = configured
            result["message"] = (
                f"连通成功：已将配置的「{configured}」解析为推理接入点「{resolved}」"
            )

        if detected:
            result.update(detected)
            result["message"] = (
                "连通成功：已检测到 Key 类型与 Base URL 不匹配，"
                f"请将「火山 Key 类型」改为 {detected['volcano_key_type']} 并保存。"
            )
            if auto_save and provider_id and detected.get("volcano_key_type"):
                LlmProviderService.apply_detected_volcano_config(
                    provider_id,
                    base_url=detected["suggested_base_url"],
                    key_type=detected["volcano_key_type"],
                )
                result["auto_saved"] = True
                result["message"] = (
                    "连通成功：已自动修正「火山 Key 类型」与 Base URL，无需手动改地址。"
                )
        return result

    @classmethod
    def _chat_completion(
        cls,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        provider_id: Optional[str],
        json_mode: bool,
    ) -> str:
        cfg = cls._config(provider_id)
        if not cfg["api_key"] or not cfg["base_url"]:
            raise LlmServiceError("LLM 配置不完整：请在后台添加并启用一个大模型")

        body = cls._build_chat_body(
            cfg=cfg,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
        timeout = cls._request_timeout(json_mode)
        retry_count = max(0, int(getattr(settings, "LLM_REQUEST_RETRIES", 2) or 2))
        max_attempts = 1 + retry_count
        last_exc: Optional[requests.RequestException] = None

        for attempt in range(1, max_attempts + 1):
            try:
                content, detected = cls._post_with_volcano_fallback(
                    cfg=cfg,
                    body=body,
                    json_mode=json_mode,
                )
                if detected:
                    logger.warning(
                        "火山 Base URL 与 Key 类型不匹配 provider=%s tried=%s ok=%s；"
                        "请在后台将 volcano_key_type 改为 %s",
                        cfg.get("provider_name"),
                        detected.get("previous_base_url"),
                        detected.get("suggested_base_url"),
                        detected.get("volcano_key_type"),
                    )
                return content
            except LlmServiceError as exc:
                status_code = cls._retryable_http_status(exc)
                if status_code and attempt < max_attempts:
                    logger.warning(
                        "LLM 服务端临时异常 provider=%s status=%s attempt=%s/%s（将重试）",
                        cfg.get("provider_name"),
                        status_code,
                        attempt,
                        max_attempts,
                    )
                    time.sleep(min(attempt * 2, 8))
                    continue
                cls._record_failed_usage(cfg)
                raise
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_exc = exc
                if attempt >= max_attempts:
                    break
                if isinstance(exc, requests.Timeout):
                    logger.warning(
                        "LLM 请求超时 provider=%s attempt=%s/%s read_timeout=%s",
                        cfg.get("provider_name"),
                        attempt,
                        max_attempts,
                        timeout[1],
                    )
                else:
                    logger.warning(
                        "LLM 连接中断 provider=%s attempt=%s/%s（将重试）",
                        cfg.get("provider_name"),
                        attempt,
                        max_attempts,
                    )
                time.sleep(min(attempt * 2, 8))
            except requests.RequestException as exc:
                last_exc = exc
                break
            except (KeyError, IndexError) as exc:
                logger.warning("LLM 响应解析失败: %s", exc)
                cls._record_failed_usage(cfg)
                raise LlmServiceError(
                    "模型返回格式异常，请确认接口为 OpenAI 兼容的 Chat Completions。"
                ) from exc

        logger.error(
            "LLM 请求失败 provider=%s model=%s base_url=%s error=%s",
            cfg.get("provider_name"),
            cfg.get("model"),
            cfg.get("base_url"),
            last_exc or "unknown",
            exc_info=last_exc,
        )
        cls._record_failed_usage(cfg)
        raise LlmServiceError(
            humanize_llm_request_error(
                last_exc, base_url=cfg.get("base_url") or "", model=cfg.get("model") or ""
            )
        ) from last_exc

    @classmethod
    def chat_completion(
        cls,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        provider_id: Optional[str],
        json_mode: bool,
    ) -> str:
        """公开 LLM 对话接口（Agent runtime 等调用方应使用此方法）。"""
        return cls._chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            provider_id=provider_id,
            json_mode=json_mode,
        )

    @classmethod
    def generate_json(
        cls,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        provider_id: Optional[str] = None,
        skip_enabled_check: bool = False,
        upstream: Optional[Dict[str, Any]] = None,
        trace_extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not skip_enabled_check and not cls.is_enabled():
            raise LlmServiceError("LLM 未启用（llm.enabled=false 或 FUSION_LLM_ENABLED=false）")

        from apps.creation.monitoring.llm_trace import (
            begin_llm_trace,
            finish_llm_trace_error,
            finish_llm_trace_success,
            is_full_llm_trace_enabled,
        )

        if is_full_llm_trace_enabled():
            begin_llm_trace(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                provider_id=provider_id,
                max_tokens=max_tokens,
                temperature=temperature,
                json_mode=True,
                upstream=upstream,
                extra=trace_extra,
            )

        content = ""
        try:
            last_parse_exc: Optional[Exception] = None
            parse_rounds = max(2, int(getattr(settings, "LLM_JSON_PARSE_RETRIES", 3) or 3))
            cfg_token_cap = max(4096, int(getattr(settings, "LLM_JSON_MAX_TOKENS_CAP", 32768) or 32768))
            base_max = max_tokens
            # token_cap 不得低于调用方显式传入的 base_max，避免重试时反而截断
            token_cap = max(cfg_token_cap, base_max or 0)
            for attempt in range(parse_rounds):
                effective_max = base_max
                if base_max and attempt > 0:
                    effective_max = min(int(base_max * (1 + 0.5 * attempt)), token_cap)
                retry_hint = ""
                if attempt > 0:
                    retry_hint = (
                        "\n\n【重要】上次输出 JSON 不完整或被截断。"
                        "请输出完整闭合的单层 JSON 对象，不要 markdown 或任何解释文字。"
                    )
                content = cls._chat_completion(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt + retry_hint,
                    temperature=temperature,
                    max_tokens=effective_max,
                    provider_id=provider_id,
                    json_mode=True,
                )
                if not (content or "").strip():
                    logger.warning("LLM JSON 返回空内容 attempt=%s", attempt + 1)
                    continue
                try:
                    parsed = cls._parse_json_content(content)
                    if is_full_llm_trace_enabled():
                        finish_llm_trace_success(raw_content=content, parsed_output=parsed)
                    return parsed
                except json.JSONDecodeError as exc:
                    last_parse_exc = exc
                    logger.warning(
                        "LLM JSON 解析失败 attempt=%s len=%s: %s",
                        attempt + 1,
                        len(content or ""),
                        exc,
                    )
            if not (content or "").strip():
                if is_full_llm_trace_enabled():
                    finish_llm_trace_error("模型返回空内容")
                raise LlmServiceError("模型返回空内容，请重试或更换模型")
            if last_parse_exc is not None:
                if is_full_llm_trace_enabled():
                    finish_llm_trace_error(str(last_parse_exc), raw_content=content)
                raise LlmServiceError(
                    humanize_user_message(
                        str(last_parse_exc),
                        default="模型输出过长被截断或 JSON 格式错误，请重试或换用输出容量更大的模型",
                    )
                ) from last_parse_exc
            parsed = cls._parse_json_content(content)
            if is_full_llm_trace_enabled():
                finish_llm_trace_success(raw_content=content, parsed_output=parsed)
            return parsed
        except LlmServiceError as exc:
            if is_full_llm_trace_enabled():
                finish_llm_trace_error(str(exc), raw_content=content)
            raise
        except Exception as exc:  # noqa: BLE001
            if is_full_llm_trace_enabled():
                finish_llm_trace_error(str(exc), raw_content=content)
            logger.exception("LLM JSON 生成失败")
            raise LlmServiceError(
                humanize_user_message(str(exc), default="模型返回解析失败，请重试或更换模型")
            ) from exc

    @classmethod
    def generate_text(
        cls,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        provider_id: Optional[str] = None,
        skip_enabled_check: bool = False,
    ) -> str:
        if not skip_enabled_check and not cls.is_enabled():
            raise LlmServiceError("LLM 未启用（llm.enabled=false 或 FUSION_LLM_ENABLED=false）")

        effective_max = max_tokens
        if effective_max is None:
            cfg = cls._config(provider_id)
            effective_max = min(2048, cfg["max_tokens"])

        return cls._chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=effective_max,
            provider_id=provider_id,
            json_mode=False,
        )

    @staticmethod
    def _strip_json_text(content: str) -> str:
        text = (content or "").strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            return fence.group(1).strip()
        open_fence = re.match(r"```(?:json)?\s*([\s\S]*)", text)
        if open_fence and text.count("```") == 1:
            return open_fence.group(1).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return text[start : end + 1]
        return text

    @staticmethod
    def _json_stack_state(text: str) -> tuple[bool, list[str]]:
        in_string = False
        escape = False
        stack: list[str] = []
        for ch in text:
            if escape:
                escape = False
                continue
            if ch == "\\" and in_string:
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                stack.append("}")
            elif ch == "[":
                stack.append("]")
            elif ch in "}]" and stack and stack[-1] == ch:
                stack.pop()
        return in_string, stack

    @staticmethod
    def _repair_truncated_json(content: str) -> str:
        """尽力闭合被 max_tokens 截断的不完整 JSON。"""
        s = LlmService._strip_json_text(content)
        if not s:
            return s

        in_string, stack = LlmService._json_stack_state(s)
        if in_string:
            s += '"'
        s = s.rstrip().rstrip(",")
        s = re.sub(r',?\s*"[^"\\]*(?:\\.[^"\\]*)*"\s*:\s*$', "", s)
        s = s.rstrip().rstrip(",")

        _, stack = LlmService._json_stack_state(s)
        while stack:
            s += stack.pop()
        return s

    @staticmethod
    def _parse_json_content(content: str) -> Dict[str, Any]:
        text = LlmService._strip_json_text(content)
        last_exc: Optional[json.JSONDecodeError] = None
        for candidate in (text, LlmService._repair_truncated_json(content)):
            if not candidate:
                continue
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError as exc:
                last_exc = exc
                continue
            if not isinstance(parsed, dict):
                raise json.JSONDecodeError("expected JSON object", candidate, 0)
            if candidate != text:
                logger.warning("LLM JSON 已通过截断修复解析，len=%s", len(candidate))
            return parsed
        if last_exc is not None:
            raise last_exc
        raise json.JSONDecodeError("empty JSON content", text or "", 0)
