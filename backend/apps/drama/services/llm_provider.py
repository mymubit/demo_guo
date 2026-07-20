# -*- coding: utf-8 -*-
"""OpenAI 兼容 LLM 提供方（优先读后台 DB 配置）。"""
from __future__ import annotations

import json
import logging
import os
import time
from enum import Enum
from typing import Any, Callable, Iterator

import requests
from django.conf import settings

from apps.drama.models import DramaLlmCallLog
from apps.drama.services.llm_call_context import get_llm_call_context
from apps.drama.services.llm_call_log_service import LlmCallLogService
from apps.drama.services.llm_config_service import LlmConfigService, ResolvedLlmConfig


def _purpose_from_context() -> str:
    ctx = get_llm_call_context()
    return (ctx.purpose if ctx else "") or ""


def _resolve_max_tokens(cfg_max_tokens: int) -> int:
    return _capped_max_tokens(cfg_max_tokens, purpose=_purpose_from_context())

logger = logging.getLogger(__name__)

# 这些接入点对 response_format=json_object 支持不完整（豆包/方舟推理接入点等）
_JSON_OBJECT_UNSUPPORTED_HOST_MARKERS = (
    "volces.com",
    "volcengineapi.com",
    "ark.cn-",
)


def _llm_timeouts() -> tuple[int, int]:
    """每次调用时读取，避免 Celery 子进程长期持有旧默认值。"""
    connect = int(
        os.environ.get(
            "LLM_CONNECT_TIMEOUT",
            str(getattr(settings, "LLM_CONNECT_TIMEOUT", 30)),
        )
    )
    read = int(
        os.environ.get(
            "LLM_READ_TIMEOUT",
            str(getattr(settings, "LLM_READ_TIMEOUT", 900)),
        )
    )
    return connect, read


def _capped_max_tokens(cfg_max_tokens: int, *, purpose: str = "") -> int:
    cap = int(getattr(settings, "LLM_COMPLETION_MAX_TOKENS", 8192))
    if purpose == "quality_scoring":
        scorer_cap = int(getattr(settings, "LLM_SCORER_MAX_TOKENS", 24576))
        cap = max(cap, scorer_cap)
    requested = int(cfg_max_tokens) if cfg_max_tokens else cap
    # 评分长文：若后台配置的 max_tokens 过小，抬到评分上限（仍受 LLM_SCORER_MAX_TOKENS 封顶）
    if purpose == "quality_scoring":
        requested = max(requested, min(cap, int(getattr(settings, "LLM_SCORER_MAX_TOKENS", 24576))))
    return max(256, min(requested, cap))


def _iter_sse_data_lines(response: requests.Response):
    """按 UTF-8 解码 SSE 行，避免 requests 误用 latin-1 造成中文乱码。"""
    response.encoding = "utf-8"
    for raw in response.iter_lines(decode_unicode=False):
        if not raw:
            continue
        try:
            line = raw.decode("utf-8")
        except UnicodeDecodeError:
            line = raw.decode("utf-8", errors="replace")
            logger.warning("SSE 行 UTF-8 解码失败，已替换非法字节")
        if not line.startswith("data:"):
            continue
        data = line[5:].lstrip()
        if data:
            yield data


def _repair_utf8_mojibake(text: str) -> str:
    """修复「UTF-8 字节被当成 latin-1 解码」的典型乱码。"""
    if not text:
        return text
    # 已含足够 CJK，基本可认定编码正确
    cjk_count = sum(1 for ch in text[:800] if "\u4e00" <= ch <= "\u9fff")
    if cjk_count >= 8:
        return text
    try:
        repaired = text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    repaired_cjk = sum(1 for ch in repaired[:800] if "\u4e00" <= ch <= "\u9fff")
    if repaired_cjk > cjk_count:
        return repaired
    return text


class LlmProviderStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    MISCONFIGURED = "misconfigured"


class LlmProviderError(Exception):
    """LLM 调用失败。"""


class LlmProvider:
    """OpenAI 兼容 HTTP 客户端：DB active 配置优先，其次 settings.LLM_*。"""

    @classmethod
    def _resolved(cls) -> ResolvedLlmConfig:
        return LlmConfigService.resolve()

    @classmethod
    def status(cls) -> LlmProviderStatus:
        cfg = cls._resolved()
        if not cfg.enabled:
            return LlmProviderStatus.DISABLED
        if not cfg.base_url or not cfg.api_key:
            return LlmProviderStatus.MISCONFIGURED
        return LlmProviderStatus.ENABLED

    @classmethod
    def _supports_json_object_format(cls, base_url: str) -> bool:
        host = (base_url or "").lower()
        return not any(marker in host for marker in _JSON_OBJECT_UNSUPPORTED_HOST_MARKERS)

    @classmethod
    def _is_json_object_unsupported_error(cls, response_text: str) -> bool:
        text = (response_text or "").lower()
        return "response_format" in text and (
            "json_object" in text or "not supported" in text or "invalidparameter" in text
        )

    @classmethod
    def chat_completion(
        cls,
        *,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        on_delta: Callable[[str, int], None] | None = None,
    ) -> dict[str, Any]:
        status = cls.status()
        if status == LlmProviderStatus.DISABLED:
            raise LlmProviderError("LLM 已禁用（后台未启用且 LLM_ENABLED=false）")
        if status == LlmProviderStatus.MISCONFIGURED:
            raise LlmProviderError("LLM 配置不完整，请在后台填写 Base URL 与 API Key")

        cfg = cls._resolved()
        use_response_format = bool(json_mode and cls._supports_json_object_format(cfg.base_url))
        # 长产物（蓝图等）用流式组装，避免整段响应卡死在读超时上
        return cls._post_chat_stream(
            cfg=cfg,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            use_response_format=use_response_format,
            allow_retry_without_format=bool(json_mode),
            on_delta=on_delta,
        )

    @classmethod
    def _post_chat_stream(
        cls,
        *,
        cfg: ResolvedLlmConfig,
        system_prompt: str,
        user_prompt: str,
        use_response_format: bool,
        allow_retry_without_format: bool,
        on_delta: Callable[[str, int], None] | None = None,
    ) -> dict[str, Any]:
        url = cls._chat_url(cfg.base_url)
        max_tokens = _resolve_max_tokens(cfg.max_tokens)
        body: dict[str, Any] = {
            "model": cfg.model,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": cfg.temperature,
            "max_tokens": max_tokens,
        }
        if use_response_format:
            body["response_format"] = {"type": "json_object"}

        started = time.monotonic()
        parts: list[str] = []
        try:
            with requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {cfg.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=_llm_timeouts(),
                stream=True,
            ) as response:
                if response.status_code >= 400:
                    err_text = (response.text or "")[:2000]
                    if (
                        allow_retry_without_format
                        and use_response_format
                        and cls._is_json_object_unsupported_error(err_text)
                    ):
                        logger.info(
                            "流式也不支持 response_format=json_object，改为普通文本 JSON 重试 base_url=%s model=%s",
                            cfg.base_url,
                            cfg.model,
                        )
                        return cls._post_chat_stream(
                            cfg=cfg,
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                            use_response_format=False,
                            allow_retry_without_format=False,
                            on_delta=on_delta,
                        )
                    latency_ms = int((time.monotonic() - started) * 1000)
                    LlmCallLogService.record(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        model_name=cfg.model,
                        base_url=cfg.base_url,
                        status=DramaLlmCallLog.Status.ERROR,
                        latency_ms=latency_ms,
                        http_status=response.status_code,
                        error_message=err_text,
                        response_text=err_text,
                    )
                    raise LlmProviderError(
                        f"LLM HTTP {response.status_code}: {err_text[:500]}"
                    )

                last_progress_at = started
                parse_failures = 0
                for data in _iter_sse_data_lines(response):
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        choices = chunk.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta") or {}
                        content = delta.get("content") or ""
                        if content:
                            parts.append(content)
                            now = time.monotonic()
                            if on_delta and now - last_progress_at >= 5:
                                on_delta("".join(parts), int((now - started) * 1000))
                                last_progress_at = now
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                        parse_failures += 1
                        if parse_failures <= 3:
                            logger.warning(
                                "忽略无法解析的 SSE 块 preview=%s",
                                data[:120],
                            )

            content = _repair_utf8_mojibake("".join(parts).strip())
            latency_ms = int((time.monotonic() - started) * 1000)
            if not content:
                LlmCallLogService.record(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model_name=cfg.model,
                    base_url=cfg.base_url,
                    status=DramaLlmCallLog.Status.ERROR,
                    latency_ms=latency_ms,
                    error_message="流式响应为空",
                )
                raise LlmProviderError("LLM 流式响应为空")

            payload = {
                "choices": [{"message": {"role": "assistant", "content": content}}],
                "model": cfg.model,
                "object": "chat.completion",
            }
            LlmCallLogService.record(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_name=cfg.model,
                base_url=cfg.base_url,
                status=DramaLlmCallLog.Status.SUCCESS,
                latency_ms=latency_ms,
                http_status=200,
                response_json=payload,
            )
            return payload
        except LlmProviderError:
            raise
        except Exception as exc:
            latency_ms = int((time.monotonic() - started) * 1000)
            LlmCallLogService.record(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_name=cfg.model,
                base_url=cfg.base_url,
                status=DramaLlmCallLog.Status.ERROR,
                latency_ms=latency_ms,
                error_message=str(exc),
            )
            raise LlmProviderError(str(exc)) from exc

    @classmethod
    def _post_chat(
        cls,
        *,
        cfg: ResolvedLlmConfig,
        system_prompt: str,
        user_prompt: str,
        use_response_format: bool,
        allow_retry_without_format: bool,
    ) -> dict[str, Any]:
        url = cls._chat_url(cfg.base_url)
        body: dict[str, Any] = {
            "model": cfg.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": cfg.temperature,
            "max_tokens": _resolve_max_tokens(cfg.max_tokens),
        }
        if use_response_format:
            body["response_format"] = {"type": "json_object"}

        started = time.monotonic()
        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {cfg.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=_llm_timeouts(),
            )
            latency_ms = int((time.monotonic() - started) * 1000)
            if response.status_code >= 400:
                if (
                    allow_retry_without_format
                    and use_response_format
                    and cls._is_json_object_unsupported_error(response.text or "")
                ):
                    logger.info(
                        "模型不支持 response_format=json_object，改为普通文本 JSON 重试 base_url=%s model=%s",
                        cfg.base_url,
                        cfg.model,
                    )
                    return cls._post_chat(
                        cfg=cfg,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        use_response_format=False,
                        allow_retry_without_format=False,
                    )
                LlmCallLogService.record(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model_name=cfg.model,
                    base_url=cfg.base_url,
                    status=DramaLlmCallLog.Status.ERROR,
                    latency_ms=latency_ms,
                    http_status=response.status_code,
                    error_message=response.text[:2000],
                    response_text=response.text[:2000],
                )
                raise LlmProviderError(
                    f"LLM HTTP {response.status_code}: {response.text[:500]}"
                )
            payload = response.json()
            LlmCallLogService.record(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_name=cfg.model,
                base_url=cfg.base_url,
                status=DramaLlmCallLog.Status.SUCCESS,
                latency_ms=latency_ms,
                http_status=response.status_code,
                response_json=payload,
            )
            return payload
        except LlmProviderError:
            raise
        except Exception as exc:
            latency_ms = int((time.monotonic() - started) * 1000)
            LlmCallLogService.record(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_name=cfg.model,
                base_url=cfg.base_url,
                status=DramaLlmCallLog.Status.ERROR,
                latency_ms=latency_ms,
                error_message=str(exc),
            )
            raise LlmProviderError(str(exc)) from exc

    @classmethod
    def stream_completion(
        cls,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> Iterator[str]:
        status = cls.status()
        if status != LlmProviderStatus.ENABLED:
            raise LlmProviderError(f"LLM 不可用: {status.value}")

        cfg = cls._resolved()
        url = cls._chat_url(cfg.base_url)
        body = {
            "model": cfg.model,
            "stream": True,
            "temperature": cfg.temperature,
            "max_tokens": _resolve_max_tokens(cfg.max_tokens),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        with requests.post(
            url,
            headers={
                "Authorization": f"Bearer {cfg.api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=_llm_timeouts(),
            stream=True,
        ) as response:
            if response.status_code >= 400:
                raise LlmProviderError(f"LLM HTTP {response.status_code}")
            for data in _iter_sse_data_lines(response):
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    piece = delta.get("content") or ""
                    if piece:
                        yield piece
                except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                    logger.warning("忽略无法解析的 SSE 块")

    @classmethod
    def _chat_url(cls, base_url: str) -> str:
        base = base_url.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"
