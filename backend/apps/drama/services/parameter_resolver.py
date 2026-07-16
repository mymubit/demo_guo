# -*- coding: utf-8 -*-
"""从 contracts/parameters.yaml 解析参数定义与选项源。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def split_source(source: str) -> tuple[str, str]:
    if "#" not in source:
        return source, ""
    file_path, dotted_path = source.split("#", 1)
    return file_path, dotted_path


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


def _normalize_option_item(item: dict[str, Any]) -> dict[str, Any]:
    option: dict[str, Any] = {
        "value": item.get("value", item.get("theme_code")),
        "label": item.get("label_zh", item.get("value")),
    }
    # 透传 UI 分层/分组元数据（与 drama-skills build/lib/source_loader.py 保持一致）
    for extra in ("tier", "category", "desc"):
        if item.get(extra) is not None:
            option[extra] = item[extra]
    return option


def normalize_options(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [
            {"value": key, "label": (item or {}).get("label_zh", key)}
            for key, item in value.items()
        ]
    if isinstance(value, list):
        return [
            _normalize_option_item(item)
            if isinstance(item, dict)
            else {"value": item, "label": str(item)}
            for item in value
        ]
    raise ValueError("选项源必须是对象或数组")


def load_yaml(root: Path, relative_path: str) -> dict[str, Any]:
    return yaml.safe_load((root / relative_path).read_text(encoding="utf-8")) or {}


def resolve_enum(spec: dict[str, Any], root: Path) -> list[Any] | None:
    if "enum" in spec:
        return list(spec["enum"])
    enum_source = spec.get("enum_source")
    if enum_source == "orchestration.*.entry_type":
        return [
            load_yaml(root, "orchestration/original-track.yaml")["entry_type"],
            load_yaml(root, "orchestration/story-adapt-track.yaml")["entry_type"],
        ]
    return None


def resolve_max_items(spec: dict[str, Any], root: Path) -> int | None:
    source = spec.get("max_items_source")
    if not source:
        return spec.get("max_items")
    return int(load_source(root, source))
