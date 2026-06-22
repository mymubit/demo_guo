# -*- coding: utf-8 -*-
"""展示文案本地化与 blocks 出口清洗。"""
from __future__ import annotations

import ast
import re
from typing import Any, List

from apps.drama.presentation.labels import FIELD_LABELS

# Episode / episode 多种英文写法 → 第N集
_EPISODE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bat the end of episode\s*(\d+)\b", re.IGNORECASE), r"第\1集末尾"),
    (re.compile(r"\bat the beginning of episode\s*(\d+)\b", re.IGNORECASE), r"第\1集开头"),
    (re.compile(r"\bthe end of episode\s*(\d+)\b", re.IGNORECASE), r"第\1集末尾"),
    (re.compile(r"\bthe beginning of episode\s*(\d+)\b", re.IGNORECASE), r"第\1集开头"),
    (re.compile(r"\bEpisode\s*(\d+)\b", re.IGNORECASE), r"第\1集"),
    (re.compile(r"\bepisode\s*(\d+)\b"), r"第\1集"),
]

_EPISODE_KEY_RE = re.compile(r"^episode_(\d+)$", re.IGNORECASE)
_RAW_DICT_LINE_RE = re.compile(r"^\s*\{")
_TIMELINE_KEYS = frozenset({"volume", "emotion", "timestamp", "transition", "speech_speed"})


def field_label(key: str) -> str:
    if _EPISODE_KEY_RE.match(key):
        return f"第{_EPISODE_KEY_RE.match(key).group(1)}集"
    return FIELD_LABELS.get(key) or FIELD_LABELS.get(key.replace("-", "_")) or key


def localize_display_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return text
    result = text.strip()
    for pattern, repl in _EPISODE_PATTERNS:
        result = pattern.sub(repl, result)
    return result


def format_inline_dict(data: dict) -> str:
    if _TIMELINE_KEYS & set(data.keys()):
        order = ("timestamp", "emotion", "volume", "speech_speed", "transition")
        parts = []
        for key in order:
            val = data.get(key)
            if val not in (None, ""):
                parts.append(f"{field_label(key)}：{val}")
        if parts:
            return " · ".join(parts)
    parts = []
    for key, val in data.items():
        if val in (None, "", [], {}):
            continue
        if isinstance(val, (str, int, float, bool)):
            parts.append(f"{field_label(str(key))}：{val}")
    return " · ".join(parts[:8]) if parts else ""


def try_format_raw_dict_string(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return text
    if not _RAW_DICT_LINE_RE.match(text):
        return localize_display_text(text)
    lines: List[str] = []
    for line in text.splitlines():
        chunk = line.strip()
        if not chunk:
            continue
        if _RAW_DICT_LINE_RE.match(chunk):
            try:
                parsed = ast.literal_eval(chunk)
            except (SyntaxError, ValueError):
                lines.append(localize_display_text(chunk))
                continue
            if isinstance(parsed, dict):
                formatted = format_inline_dict(parsed)
                lines.append(formatted if formatted else chunk)
            else:
                lines.append(localize_display_text(str(parsed)))
        else:
            lines.append(localize_display_text(chunk))
    return "\n".join(lines)


def sanitize_display_string(text: str) -> str:
    return try_format_raw_dict_string(localize_display_text(text))


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_display_string(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_value(item) for key, item in value.items()}
    return value


def sanitize_blocks(blocks: List[dict]) -> List[dict]:
    """统一清洗 blocks 内所有展示字符串（Episode 本地化、裸 dict 格式化）。"""
    return _sanitize_value(blocks)
