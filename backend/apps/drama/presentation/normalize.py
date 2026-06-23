# -*- coding: utf-8 -*-
"""产物 payload 归一化 — 兼容 Drama 各 schema 的多种包裹字段。"""
from __future__ import annotations

from typing import Any

META_KEYS = frozenset({"_meta", "artifact_key", "schemaVersion", "schema_version"})

# LLM 常见内容包裹键（按优先级尝试展开）
CONTENT_WRAPPER_KEYS = (
    "data",
    "project_content",
    "world_data",
    "audit_result",
    "content",
    "report",
    "result",
    "analysis",
    "report_data",
    "payload",
)


def normalize_payload(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload

    for wrap_key in CONTENT_WRAPPER_KEYS:
        inner = payload.get(wrap_key)
        if isinstance(inner, dict) and inner:
            merged = {k: v for k, v in payload.items() if k not in META_KEYS and k != wrap_key}
            merged.update(inner)
            return normalize_payload(merged)

    return {k: v for k, v in payload.items() if k not in META_KEYS}


def _format_list_brief(items: list, *, limit: int = 10) -> str:
    parts: list[str] = []
    for item in items[:limit]:
        if isinstance(item, str) and item.strip():
            parts.append(item.strip())
        elif isinstance(item, dict):
            inner = " · ".join(
                f"{k}：{v}"
                for k, v in list(item.items())[:5]
                if v not in (None, "", [], {})
            )
            if inner:
                parts.append(inner)
        elif item not in (None, "", [], {}):
            parts.append(str(item))
    return "；".join(parts) if parts else "—"


def _format_dict_brief(data: dict, *, limit: int = 12) -> str:
    parts: list[str] = []
    for key, val in list(data.items())[:limit]:
        if val in (None, "", [], {}):
            continue
        if isinstance(val, (str, int, float, bool)):
            parts.append(f"{key}：{format_scalar(val)}")
        elif isinstance(val, list):
            parts.append(f"{key}：{_format_list_brief(val)}")
        elif isinstance(val, dict):
            parts.append(f"{key}：{_format_dict_brief(val, limit=6)}")
    return "；".join(parts) if parts else "—"


def format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if value is None:
        return "—"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value == int(value):
            return str(int(value))
        return str(value)
    if isinstance(value, list):
        return _format_list_brief(value)
    if isinstance(value, dict):
        return _format_dict_brief(value)
    return str(value).strip()
