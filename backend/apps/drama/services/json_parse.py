# -*- coding: utf-8 -*-
"""LLM 输出 JSON 解析（允许剥离 markdown 围栏，禁止伪造字段）。"""
from __future__ import annotations

import json
import re
from typing import Any

from apps.core.exceptions import SCHEMA_VALIDATION_FAILED, BusinessException

_FENCE_RE = re.compile(
    r"^```(?:json)?\s*\n?(.*?)\n?```\s*$",
    re.DOTALL | re.IGNORECASE,
)


class JsonParseError(ValueError):
    """JSON 解析失败。"""


def strip_markdown_fence(content: str) -> str:
    """剥离可选的 markdown JSON 代码围栏。"""
    text = content.strip()
    match = _FENCE_RE.match(text)
    if match:
        return match.group(1).strip()
    return text


def parse_llm_json(content: str) -> dict[str, Any]:
    """解析 LLM 返回的 JSON 对象。"""
    text = strip_markdown_fence(content)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise JsonParseError(f"LLM 输出不是合法 JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise JsonParseError("LLM 输出必须是 JSON 对象")
    return parsed


def parse_and_validate(
    content: str,
    *,
    validator,
    schema_path: str,
) -> dict[str, Any]:
    """解析 JSON 并用指定 schema 校验，禁止在解析阶段注入额外字段。"""
    payload = parse_llm_json(content)
    try:
        validator.validate_file(payload, schema_path)
    except BusinessException:
        raise
    except Exception as exc:
        raise BusinessException(
            SCHEMA_VALIDATION_FAILED,
            f"产物 Schema 校验失败: {exc}",
            http_status=422,
        ) from exc
    return payload
