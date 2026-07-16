# -*- coding: utf-8 -*-
"""OpenAI 兼容 LLM 提供方（优先读后台 DB 配置）。"""
from __future__ import annotations

import json
import logging
from enum import Enum
from typing import Any, Iterator

import requests
from django.conf import settings

from apps.drama.services.llm_config_service import LlmConfigService, ResolvedLlmConfig

logger = logging.getLogger(__name__)


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
    def chat_completion(
        cls,
        *,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
    ) -> dict[str, Any]:
        status = cls.status()
        if status == LlmProviderStatus.DISABLED:
            raise LlmProviderError("LLM 已禁用（后台未启用且 LLM_ENABLED=false）")
        if status == LlmProviderStatus.MISCONFIGURED:
            raise LlmProviderError("LLM 配置不完整，请在后台填写 Base URL 与 API Key")

        cfg = cls._resolved()
        url = cls._chat_url(cfg.base_url)
        body: dict[str, Any] = {
            "model": cfg.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {cfg.api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=(settings.LLM_CONNECT_TIMEOUT, settings.LLM_READ_TIMEOUT),
        )
        if response.status_code >= 400:
            raise LlmProviderError(
                f"LLM HTTP {response.status_code}: {response.text[:500]}"
            )
        return response.json()

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
            "max_tokens": cfg.max_tokens,
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
            timeout=(settings.LLM_CONNECT_TIMEOUT, settings.LLM_READ_TIMEOUT),
            stream=True,
        ) as response:
            if response.status_code >= 400:
                raise LlmProviderError(f"LLM HTTP {response.status_code}")
            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    logger.warning("忽略无法解析的 SSE 块")

    @classmethod
    def _chat_url(cls, base_url: str) -> str:
        base = base_url.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"
