"""从 contracts/parameters.yaml 解析参数定义（工作台导出与 Schema 生成共用）。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from lib.source_loader import load_source

ROOT = Path(__file__).resolve().parents[2]


def load_yaml(relative_path: str, root: Optional[Path] = None) -> Dict[str, Any]:
    base = root or ROOT
    return yaml.safe_load((base / relative_path).read_text(encoding="utf-8")) or {}


def resolve_enum(spec: Dict[str, Any], root: Optional[Path] = None) -> Optional[List[Any]]:
    base = root or ROOT
    if "enum" in spec:
        return list(spec["enum"])
    enum_source = spec.get("enum_source")
    if enum_source == "orchestration.*.entry_type":
        return [
            load_yaml("orchestration/original-track.yaml", base)["entry_type"],
            load_yaml("orchestration/story-adapt-track.yaml", base)["entry_type"],
        ]
    return None


def resolve_max_items(spec: Dict[str, Any], root: Optional[Path] = None) -> Optional[int]:
    source = spec.get("max_items_source")
    if not source:
        return spec.get("max_items")
    return int(load_source(root or ROOT, source))


def resolve_parameter_schema_fragment(
    name: str, spec: Dict[str, Any], root: Optional[Path] = None
) -> Dict[str, Any]:
    """将单个参数契约条目转为 JSON Schema 片段（不含 $ref 包装）。"""
    base = root or ROOT
    param_type = spec.get("type")
    if not param_type:
        raise ValueError(f"参数 {name} 缺少 type")

    if name == "genre_matrix":
        matrix = load_yaml("foundation/theme-matrix.yaml", base)
        dim_order = list(matrix.get("dim_order") or [])
        return {
            "type": "object",
            "required": dim_order,
            "properties": {axis: {"type": "string"} for axis in dim_order},
            "additionalProperties": False,
        }

    schema: Dict[str, Any] = {}
    if spec.get("nullable"):
        schema["type"] = [param_type, "null"]
    else:
        schema["type"] = param_type

    enum_values = resolve_enum(spec, base)
    if enum_values is not None:
        schema["enum"] = sorted(enum_values) if all(isinstance(v, str) for v in enum_values) else enum_values

    if "minimum" in spec:
        schema["minimum"] = spec["minimum"]
    if "maximum" in spec:
        schema["maximum"] = spec["maximum"]
    if "pattern" in spec:
        schema["pattern"] = spec["pattern"]
    if "min_length" in spec:
        schema["minLength"] = spec["min_length"]
    if spec.get("unique_items"):
        schema["uniqueItems"] = True

    max_items = resolve_max_items(spec, base)
    if max_items is not None:
        schema["maxItems"] = max_items

    if param_type == "array":
        items: Dict[str, Any] = {}
        if "items_type" in spec:
            items["type"] = spec["items_type"]
        if "enum_items" in spec:
            items["enum"] = sorted(spec["enum_items"])
        if items:
            schema["items"] = items

    if param_type == "object":
        nested = spec.get("properties") or {}
        if nested:
            schema["properties"] = {
                key: resolve_parameter_schema_fragment(
                    f"{name}.{key}",
                    {"type": child.get("type"), **child},
                    base,
                )
                for key, child in sorted(nested.items())
            }
            schema["additionalProperties"] = False

    if "default" in spec:
        schema["default"] = spec["default"]

    return schema
