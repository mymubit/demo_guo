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
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


class JsonParseError(ValueError):
    """JSON 解析失败。"""


def strip_markdown_fence(content: str) -> str:
    """剥离可选的 markdown JSON 代码围栏。"""
    text = content.strip()
    match = _FENCE_RE.match(text)
    if match:
        return match.group(1).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text, count=1, flags=re.IGNORECASE)
        text = re.sub(r"\n?```\s*$", "", text)
        return text.strip()
    return text


def _repair_trailing_comma(text: str) -> str:
    """修复模型常见尾逗号。"""
    return _TRAILING_COMMA_RE.sub(r"\1", text)


def parse_llm_json(content: str) -> dict[str, Any]:
    """解析 LLM 返回的 JSON 对象。"""
    text = strip_markdown_fence(_repair_utf8_mojibake(content))
    last_error: Exception | None = None
    for attempt in (text, _repair_trailing_comma(text)):
        try:
            parsed = json.loads(attempt)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if not isinstance(parsed, dict):
            raise JsonParseError("LLM 输出必须是 JSON 对象")
        return parsed

    detail = f": {last_error}" if last_error else ""
    raise JsonParseError(f"LLM 输出不是合法 JSON{detail}")


def _repair_utf8_mojibake(text: str) -> str:
    """修复 UTF-8 被误按 latin-1 解码的乱码。"""
    if not text:
        return text
    cjk_count = sum(1 for ch in text[:800] if "\u4e00" <= ch <= "\u9fff")
    if cjk_count >= 8:
        return text
    try:
        repaired = text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    repaired_cjk = sum(1 for ch in repaired[:800] if "\u4e00" <= ch <= "\u9fff")
    return repaired if repaired_cjk > cjk_count else text


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
