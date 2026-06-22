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


def format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if value is None:
        return "—"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value == int(value):
            return str(int(value))
        return str(value)
    return str(value).strip()
