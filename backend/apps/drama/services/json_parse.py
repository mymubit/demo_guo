# -*- coding: utf-8 -*-
"""LLM 输出 JSON 解析（允许剥离 markdown 围栏，禁止伪造字段）。

汲取 LangChain structured output 的务实做法（不引入框架）：
1. 从夹杂说明文字的回复中抽取 JSON 对象
2. 轻量修复常见语法瑕疵（如尾逗号）
3. 为「校验失败后单次纠错」提供 prompt 片段
"""
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
_REPAIR_CONTENT_MAX_CHARS = 8000


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


def extract_json_object(text: str) -> str | None:
    """从混杂文本中按括号平衡抽取第一个可解析的 JSON 对象。"""
    for start in _object_start_indexes(text):
        extracted = _slice_balanced_object(text, start)
        if extracted is None:
            continue
        try:
            parsed = json.loads(extracted)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return extracted
    return None


def _object_start_indexes(text: str) -> list[int]:
    return [index for index, ch in enumerate(text) if ch == "{"]


def _slice_balanced_object(text: str, start: int) -> str | None:
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        ch = text[index]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def light_repair_json(text: str) -> str:
    """修复模型常见 JSON 瑕疵：尾逗号、JS 注释、简单单引号键/值。"""
    repaired = text
    # 去掉 // 行注释与 /* */ 块注释（字符串外粗修，优先处理模型胡写注释）
    repaired = re.sub(r"/\*.*?\*/", "", repaired, flags=re.DOTALL)
    repaired = re.sub(r"(?m)^\s*//.*?$", "", repaired)
    repaired = _TRAILING_COMMA_RE.sub(r"\1", repaired)
    # {"key": 'value'} 或 {'key': "value"} 的简单单引号（避免破坏含撇号的中文引号场景时较保守）
    if "'" in repaired and '"' in repaired:
        repaired = re.sub(r"'([^'\\]*)'", r'"\1"', repaired)
    return repaired


def parse_llm_json(content: str) -> dict[str, Any]:
    """解析 LLM 返回的 JSON 对象。"""
    text = strip_markdown_fence(_repair_utf8_mojibake(content))
    candidates: list[str] = [text]
    # 正文中部的 ```json 围栏
    fence_match = re.search(
        r"```(?:json)?\s*\n?(.*?)\n?```",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if fence_match:
        fenced = fence_match.group(1).strip()
        if fenced not in candidates:
            candidates.append(fenced)
    extracted = extract_json_object(text)
    if extracted and extracted not in candidates:
        candidates.append(extracted)

    last_error: Exception | None = None
    seen: set[str] = set()
    for candidate in candidates:
        for attempt in (candidate, light_repair_json(candidate)):
            if attempt in seen:
                continue
            seen.add(attempt)
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


def build_json_repair_user_prompt(
    *,
    raw_content: str,
    error_message: str,
    required_fields: list[str] | None = None,
) -> str:
    """构造「单次纠错」用户提示（对齐 OutputFixingParser 思路）。"""
    snippet = (raw_content or "").strip()
    if len(snippet) > _REPAIR_CONTENT_MAX_CHARS:
        snippet = snippet[:_REPAIR_CONTENT_MAX_CHARS] + "\n…(已截断)"
    lines = [
        "你上一次输出的内容无法解析为合规 JSON 对象，或未通过产物 Schema 校验。",
        f"错误信息：{error_message}",
        "请仅输出修正后的合法 JSON 对象：不要解释、不要 markdown 代码围栏、不要前后缀文字。",
    ]
    if required_fields:
        lines.append("必填字段：" + ", ".join(required_fields))
    lines.extend(["", "上一次原始输出：", snippet])
    return "\n".join(lines)


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
