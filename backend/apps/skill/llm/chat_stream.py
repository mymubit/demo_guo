# -*- coding: utf-8 -*-
"""OpenAI 兼容 Chat Completions 流式接口。"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterator, Optional, Tuple

import requests
from django.conf import settings

from apps.common.user_messages import humanize_llm_request_error
from apps.skill.llm.chat import LlmService, LlmServiceError
from apps.skill.llm.usage_log import LlmUsageService

logger = logging.getLogger(__name__)


class LlmStreamError(LlmServiceError):
    pass


def _iter_sse_data_lines(resp: requests.Response) -> Iterator[str]:
    for raw_line in resp.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        line = raw_line.strip()
        if line == "data: [DONE]":
            return
        if line.startswith("data:"):
            yield line[5:].strip()


def iter_chat_completion_stream(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: Optional[float],
    max_tokens: Optional[int],
    provider_id: Optional[str],
    json_mode: bool = True,
    fallback_provider_ids: Optional[list[str]] = None,
) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """逐 token yield `(delta_text, usage_snapshot)`；主 provider 失败时尝试 fallback。"""
    provider_chain = [provider_id] if provider_id else []
    for fb in fallback_provider_ids or []:
        if fb and fb not in provider_chain:
            provider_chain.append(fb)

    last_error: Optional[Exception] = None
    for idx, active_provider in enumerate(provider_chain or [None]):
        try:
            yield from _iter_chat_completion_stream_once(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                provider_id=active_provider,
                json_mode=json_mode,
            )
            return
        except LlmStreamError as exc:
            last_error = exc
            if idx >= len(provider_chain) - 1:
                raise
            logger.warning(
                "LLM stream provider=%s failed, trying fallback: %s",
                active_provider,
                provider_chain[idx + 1] if idx + 1 < len(provider_chain) else "",
            )
    if last_error:
        raise last_error


def _iter_chat_completion_stream_once(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: Optional[float],
    max_tokens: Optional[int],
    provider_id: Optional[str],
    json_mode: bool,
) -> Iterator[Tuple[str, Dict[str, Any]]]:
    cfg = LlmService._config(provider_id)  # noqa: SLF001
    if not cfg.get("api_key") or not cfg.get("base_url"):
        raise LlmStreamError("LLM 配置不完整：请在后台添加并启用一个大模型")

    body = LlmService._build_chat_body(  # noqa: SLF001
        cfg=cfg,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=json_mode,
    )
    body["stream"] = True
    url = LlmService._chat_completions_url(cfg["base_url"])  # noqa: SLF001
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    timeout = LlmService._request_timeout(json_mode)  # noqa: SLF001

    full_parts: list[str] = []
    usage: Dict[str, Any] = {}
    try:
        with requests.post(url, headers=headers, json=body, timeout=timeout, stream=True) as resp:
            resp.raise_for_status()
            for payload in _iter_sse_data_lines(resp):
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                if isinstance(event.get("usage"), dict):
                    usage = event["usage"]
                choices = event.get("choices") or []
                if not choices:
                    continue
                choice = choices[0] if isinstance(choices[0], dict) else {}
                delta = choice.get("delta") or {}
                text = delta.get("content") or ""
                if text:
                    full_parts.append(text)
                    yield text, dict(usage)
    except requests.HTTPError as exc:
        LlmUsageService.record(cfg=cfg, usage={}, success=False)
        raise LlmStreamError(
            humanize_llm_request_error(
                exc,
                base_url=cfg.get("base_url") or "",
                model=cfg.get("model") or "",
                response_body=(getattr(getattr(exc, "response", None), "text", "") or "")[:500],
            )
        ) from exc
    except requests.RequestException as exc:
        LlmUsageService.record(cfg=cfg, usage={}, success=False)
        raise LlmStreamError(
            humanize_llm_request_error(
                exc,
                base_url=cfg.get("base_url") or "",
                model=cfg.get("model") or "",
            )
        ) from exc

    if usage:
        LlmUsageService.record(cfg=cfg, usage=usage, success=True)
    yield "", dict(usage)


def collect_chat_completion_stream(**kwargs: Any) -> Tuple[str, Dict[str, Any]]:
    """非流式消费，返回完整文本与 usage。"""
    parts: list[str] = []
    usage: Dict[str, Any] = {}
    for delta, snap in iter_chat_completion_stream(**kwargs):
        if delta:
            parts.append(delta)
        if snap:
            usage = snap
    return "".join(parts), usage
