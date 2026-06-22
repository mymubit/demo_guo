# -*- coding: utf-8 -*-
"""LLM JSON 输出自修复（独立 Agent runtime）。"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, Tuple

from django.conf import settings

from apps.creation.agent_runtime.independent_service import AgentRuntimeError, extract_json_object
from apps.skill.llm.chat import LlmService

logger = logging.getLogger(__name__)

MAX_JSON_HEAL_ATTEMPTS = 2


def _schema_hint(agent) -> str:
    contract = getattr(agent, "output_contract", None) or {}
    parts = [f"schema_version={contract.get('schema_version', '')}"]
    artifacts = contract.get("artifacts") or []
    if artifacts:
        parts.append(f"allowed artifact keys: {', '.join(str(k) for k in artifacts)}")
    return "; ".join(p for p in parts if p)


def parse_json_with_self_heal(
    raw: str,
    *,
    agent,
    system_prompt: str,
    user_prompt: str,
    temperature: Optional[float],
    max_tokens: Optional[int],
    provider_id: Optional[str],
) -> Tuple[Dict[str, Any], int]:
    """解析 JSON；格式错误时最多重试 MAX_JSON_HEAL_ATTEMPTS 次修复 LLM。"""
    last_error = ""
    heal_attempts = 0
    current_raw = raw or ""
    for attempt in range(MAX_JSON_HEAL_ATTEMPTS + 1):
        try:
            return extract_json_object(current_raw), heal_attempts
        except AgentRuntimeError as exc:
            last_error = str(exc)
            if attempt >= MAX_JSON_HEAL_ATTEMPTS:
                break
            heal_attempts += 1
            heal_user = (
                f"{user_prompt}\n\n"
                "【JSON 修复任务】上次模型输出无法解析为合法 JSON 对象。\n"
                f"解析错误：{last_error}\n"
                f"Schema 要求：{_schema_hint(agent)}\n"
                f"上次输出片段（供修复）：\n{current_raw[:8000]}\n"
                "请只输出一个完整闭合的 JSON 对象，不要 markdown 或解释。"
            )
            try:
                current_raw = LlmService.chat_completion(
                    system_prompt=system_prompt or "你是 JSON 修复助手。",
                    user_prompt=heal_user,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    provider_id=provider_id,
                    json_mode=True,
                )
            except Exception as heal_exc:  # noqa: BLE001
                logger.warning("[JsonSelfHeal] heal LLM failed agent=%s: %s", agent.agent_id, heal_exc)
                break
    raise AgentRuntimeError(f"模型输出不是合法 JSON：{last_error}")
