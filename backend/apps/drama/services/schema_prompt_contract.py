from __future__ import annotations

from typing import Any


def extract_required_paths(
    schema: dict[str, Any],
    *,
    max_paths: int = 80,
) -> list[str]:
    """递归抽取 JSON Schema required 路径（含数组 items）。"""
    paths: list[str] = []
    _walk_object(schema, prefix="", out=paths, max_paths=max_paths)
    # 去重且保持稳定顺序
    seen: set[str] = set()
    ordered: list[str] = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered[:max_paths]


def _walk_object(
    schema: dict[str, Any],
    *,
    prefix: str,
    out: list[str],
    max_paths: int,
) -> None:
    if len(out) >= max_paths:
        return
    if not isinstance(schema, dict):
        return
    required = schema.get("required") or []
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for key in required:
        key_s = str(key)
        path = f"{prefix}.{key_s}" if prefix else key_s
        out.append(path)
        if len(out) >= max_paths:
            return
        child = props.get(key_s)
        if isinstance(child, dict):
            _walk_node(child, prefix=path, out=out, max_paths=max_paths)


def _walk_node(
    schema: dict[str, Any],
    *,
    prefix: str,
    out: list[str],
    max_paths: int,
) -> None:
    if len(out) >= max_paths:
        return
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema or "required" in schema:
        _walk_object(schema, prefix=prefix, out=out, max_paths=max_paths)
        return
    if schema_type == "array" or "items" in schema:
        items = schema.get("items")
        if isinstance(items, dict):
            _walk_node(items, prefix=f"{prefix}[]", out=out, max_paths=max_paths)
