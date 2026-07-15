"""解析 workbench 中的 options_source / fields_source。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


def split_source(source: str) -> Tuple[str, str]:
    if "#" not in source:
        return source, ""
    return tuple(source.split("#", 1))  # type: ignore[return-value]


def resolve_path(value: Any, dotted_path: str) -> Any:
    current = value
    if not dotted_path:
        return current
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_path)
        current = current[part]
    return current


def load_source(root: Path, source: str) -> Any:
    file_path, dotted_path = split_source(source)
    value = yaml.safe_load((root / file_path).read_text(encoding="utf-8")) or {}
    return resolve_path(value, dotted_path)


def normalize_options(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, dict):
        return [
            {"value": key, "label": (item or {}).get("label_zh", key)}
            for key, item in value.items()
        ]
    if isinstance(value, list):
        return [
            {
                "value": item.get("value", item.get("theme_code")),
                "label": item.get("label_zh", item.get("value")),
            }
            if isinstance(item, dict)
            else {"value": item, "label": str(item)}
            for item in value
        ]
    raise ValueError("选项源必须是对象或数组")
