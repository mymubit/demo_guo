"""工作台条件表达式安全求值器。"""
from __future__ import annotations

import re
from typing import Any, Dict

COMPARISON = re.compile(
    r"^(?P<path>[A-Za-z_][A-Za-z0-9_.]*)\s*==\s*(?P<value>.+)$"
)
CONTAINS = re.compile(
    r"^(?P<path>[A-Za-z_][A-Za-z0-9_.]*)\s+contains\s+(?P<value>.+)$"
)
NOT_EMPTY = re.compile(
    r"^(?P<path>[A-Za-z_][A-Za-z0-9_.]*)\s+is\s+not\s+empty$"
)


def deep_get(data: Dict[str, Any], path: str) -> Any:
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


def evaluate(expression: str, context: Dict[str, Any]) -> bool:
    comparison = COMPARISON.match(expression.strip())
    if comparison:
        return deep_get(context, comparison["path"]) == parse_literal(
            comparison["value"]
        )
    contains = CONTAINS.match(expression.strip())
    if contains:
        collection = deep_get(context, contains["path"])
        expected = parse_literal(contains["value"])
        return isinstance(collection, (list, tuple, set, str)) and expected in collection
    not_empty = NOT_EMPTY.match(expression.strip())
    if not_empty:
        return _is_nonempty(deep_get(context, not_empty["path"]))
    raise ValueError(f"不支持的条件表达式: {expression}")
