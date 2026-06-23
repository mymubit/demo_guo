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
    normalized = key.replace("-", "_")
    return FIELD_LABELS.get(key) or FIELD_LABELS.get(normalized) or key


def localize_role_label(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    raw = str(value).strip()
    if not raw:
        return ""
    if any("\u4e00" <= char <= "\u9fff" for char in raw):
        return raw
    phrase = localize_phrase_label(raw)
    if phrase and phrase != raw:
        return phrase
    normalized = raw.replace("-", "_").lower()
    if normalized in FIELD_LABELS:
        return FIELD_LABELS[normalized]
    if normalized.startswith("protagonist"):
        if "female" in normalized:
            return "女主"
        if "male" in normalized:
            return "男主"
        return "主角"
    if normalized.startswith("antagonist"):
        if "main" in normalized:
            return "核心反派"
        return "反派"
    if normalized.endswith("_antagonist") or "_antagonist" in normalized:
        if normalized.startswith("main_"):
            return "核心反派"
        if normalized.startswith("secondary_"):
            return "次要反派"
        if normalized.startswith("tertiary_"):
            return "帮凶"
        return "反派"
    if normalized.startswith("supporting"):
        return "配角"
    return FIELD_LABELS.get(normalized, "")


def _normalize_phrase_key(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower().replace("_", "-"))


def _localize_single_phrase(raw: str) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    if any("\u4e00" <= char <= "\u9fff" for char in text):
        return text

    for candidate in (text, text.lower(), _normalize_phrase_key(text)):
        if candidate in FIELD_LABELS:
            return FIELD_LABELS[candidate]
        spaced = candidate.replace("-", " ")
        if spaced in FIELD_LABELS:
            return FIELD_LABELS[spaced]

    normalized = text.replace("-", "_").lower()
    if normalized in FIELD_LABELS:
        return FIELD_LABELS[normalized]
    if normalized.startswith("protagonist"):
        return "女主" if "female" in normalized else "男主" if "male" in normalized else "主角"
    if normalized.endswith("_antagonist") or "_antagonist" in normalized:
        if normalized.startswith("main_"):
            return "核心反派"
        if normalized.startswith("secondary_"):
            return "次要反派"
        if normalized.startswith("tertiary_"):
            return "帮凶"
        return "反派"
    if normalized.startswith("antagonist"):
        return "核心反派" if "main" in normalized else "反派"
    if normalized.startswith("supporting"):
        return "配角"
    return ""


def localize_phrase_label(value: Any) -> str:
    """将 slash/箭头 连接的英文短语转为中文（关系类型、角色定位等）。"""
    if value in (None, "", [], {}):
        return ""
    raw = str(value).strip()
    if not raw:
        return ""
    if any("\u4e00" <= char <= "\u9fff" for char in raw):
        return raw

    whole = _localize_single_phrase(raw)
    if whole:
        return whole

    if re.search(r"[/→|]", raw):
        parts = [part.strip() for part in re.split(r"\s*[/→|]\s*", raw) if part.strip()]
        localized_parts = [_localize_single_phrase(part) for part in parts]
        if any(localized_parts):
            return " / ".join(part for part in localized_parts if part)

    return ""


def relationship_type_label(item: dict) -> str:
    """仅依据 relationship_type 字段本地化，不做推断或别名兜底。"""
    if not isinstance(item, dict):
        return ""
    val = item.get("relationship_type")
    if val in (None, "", [], {}):
        return ""
    return localize_phrase_label(str(val))


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


def parse_enumerated_prose(text: str, *, min_items: int = 2) -> list[str]:
    """将「1. … 2. …」或换行/分号分隔的长文本拆成列表项。"""
    if not isinstance(text, str) or not text.strip():
        return []
    raw = text.strip().replace("\r\n", "\n")

    if re.search(r"\d+\.\s*\S", raw):
        parts = re.split(r"(?=\d+\.\s*)", raw)
        items: list[str] = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            part = re.sub(r"^\d+\.\s*", "", part).strip()
            if part:
                items.append(part)
        if len(items) >= min_items:
            return items

    if "\n" in raw:
        lines = [
            re.sub(r"^\d+\.\s*", "", ln.strip()).strip()
            for ln in raw.splitlines()
            if ln.strip()
        ]
        if len(lines) >= min_items:
            return lines

    if raw.count("；") >= min_items - 1:
        parts = [p.strip() for p in raw.split("；") if p.strip()]
        parts = [re.sub(r"^\d+\.\s*", "", p).strip() for p in parts]
        if len(parts) >= min_items:
            return parts

    return []


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
