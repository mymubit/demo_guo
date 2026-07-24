# -*- coding: utf-8 -*-
"""工作台/模块条件表达式安全求值（对齐 drama-skills/tools/lib/condition_eval.py）。"""
from __future__ import annotations

import re
from typing import Any

_COMPARISON = re.compile(
    r"^(?P<path>[A-Za-z_][A-Za-z0-9_.]*)\s*==\s*(?P<value>.+)$"
)
_CONTAINS = re.compile(
    r"^(?P<path>[A-Za-z_][A-Za-z0-9_.]*)\s+contains\s+(?P<value>.+)$"
)
_NOT_EMPTY = re.compile(
    r"^(?P<path>[A-Za-z_][A-Za-z0-9_.]*)\s+is\s+not\s+empty$"
)


def deep_get(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def parse_literal(raw: str) -> Any:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "null":
        return None
    try:
        return int(value)
    except ValueError:
        return value


def _is_nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple, set, dict, str)):
        return len(value) > 0
    return True


def evaluate_condition(expression: str, context: dict[str, Any]) -> bool:
    comparison = _COMPARISON.match(expression.strip())
    if comparison:
        return deep_get(context, comparison["path"]) == parse_literal(
            comparison["value"]
        )
    contains = _CONTAINS.match(expression.strip())
    if contains:
        collection = deep_get(context, contains["path"])
        expected = parse_literal(contains["value"])
        return isinstance(collection, (list, tuple, set, str)) and expected in collection
    not_empty = _NOT_EMPTY.match(expression.strip())
    if not_empty:
        return _is_nonempty(deep_get(context, not_empty["path"]))
    raise ValueError(f"不支持的条件表达式: {expression}")


def module_enable_context(settings: dict[str, Any] | None) -> dict[str, Any]:
    """构造模块 enable_when 求值上下文。"""
    settings = settings or {}
    prefs = settings.get("creation_preferences") or {}
    deliverables = prefs.get("deliverables") or []
    refs = settings.get("reference_dramas") or []
    return {
        "entry_type": settings.get("entry_type"),
        "deliverables": deliverables,
        "target_platform": settings.get("target_platform"),
        "audience_channel": settings.get("audience_channel"),
        "creation_preferences": prefs,
        "reference_dramas": refs,
    }
