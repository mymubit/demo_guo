from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from apps.drama.services.skills_loader import SkillsBundleLoader


def load_artifact_fixture(
    loader: "SkillsBundleLoader", artifact_key: str
) -> dict[str, Any] | None:
    """从 build/fixtures/artifacts/valid-artifacts.json 读取产物示例。

    生产代码通过 loader 读取技能仓，避免直接 import apps.drama.tests.helpers。
    """
    try:
        data = loader.load_json("build/fixtures/artifacts/valid-artifacts.json")
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    item = data.get(artifact_key)
    return item if isinstance(item, dict) else None


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


def build_output_skeleton(
    schema: dict[str, Any],
    *,
    fixture: dict[str, Any] | None = None,
    max_chars: int = 3500,
) -> dict[str, Any]:
    """根据 schema 生成最小合法输出骨架：优先用 fixture 裁剪，否则按 type 填占位。"""
    if fixture is not None:
        skeleton = _prune_to_schema(deepcopy(fixture), schema)
    else:
        skeleton = _synthesize_from_schema(schema)
    blob = json.dumps(skeleton, ensure_ascii=False)
    if len(blob) > max_chars:
        skeleton = _shrink_strings(skeleton, max_chars=max_chars, schema=schema)
    return skeleton


def render_contract_block(
    artifact_key: str,
    schema: dict[str, Any],
    *,
    fixture: dict[str, Any] | None = None,
    max_chars: int = 3500,
) -> str:
    """返回可拼进 system prompt 的 Markdown 契约块。"""
    paths = extract_required_paths(schema)
    skeleton = build_output_skeleton(schema, fixture=fixture, max_chars=max_chars)
    example = json.dumps(skeleton, ensure_ascii=False, indent=2)
    lines = [
        f"- artifact_key: {artifact_key}",
        "- 下列字段名必须原样使用（禁止 want/need/open_hook 等别名键）：",
        "- 必填路径:",
        *[f"  - {path}" for path in paths],
        "- 最小合法示例（键名写死，可改文案不可改键名）：",
        "```json",
        example,
        "```",
        "- 仅输出一个 JSON 对象；不要 markdown 围栏；不要 schema 外字段。",
    ]
    return "\n".join(lines)


def _schema_kind(schema: dict[str, Any]) -> str:
    """判断 schema 主类型：object / array / 基础类型。"""
    if not isinstance(schema, dict):
        return "any"
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        for t in schema_type:
            if t != "null":
                return t
        return "any"
    if schema_type in ("object", "array"):
        return schema_type
    if "properties" in schema or "required" in schema:
        return "object"
    if "items" in schema:
        return "array"
    if schema_type in ("string", "integer", "number", "boolean"):
        return schema_type
    if "enum" in schema:
        return "enum"
    return "any"


def _prune_to_schema(value: Any, schema: dict[str, Any]) -> Any:
    kind = _schema_kind(schema)
    if kind == "object":
        return _prune_object(value, schema)
    if kind == "array":
        return _prune_array(value, schema)
    return _prune_primitive(value, schema)


def _prune_object(value: Any, schema: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return _synthesize_from_schema(schema)
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required = schema.get("required") or []
    additional_props_false = schema.get("additionalProperties") is False
    result: dict[str, Any] = {}
    for key, child_schema in props.items():
        if key in value:
            result[key] = _prune_to_schema(value[key], child_schema)
    for key in required:
        if key not in result:
            child = props.get(key, {})
            result[key] = _synthesize_from_schema(child if isinstance(child, dict) else {})
    if not additional_props_false:
        for key, val in value.items():
            if key not in result:
                result[key] = val
    return result


def _prune_array(value: Any, schema: dict[str, Any]) -> list[Any]:
    if not isinstance(value, list):
        return _synthesize_from_schema(schema)
    items_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
    pruned = [_prune_to_schema(item, items_schema) for item in value]
    min_items = schema.get("minItems")
    max_items = schema.get("maxItems")
    if isinstance(min_items, int) and len(pruned) < min_items:
        while len(pruned) < min_items:
            pruned.append(_synthesize_from_schema(items_schema))
    if isinstance(max_items, int) and len(pruned) > max_items:
        pruned = pruned[:max_items]
    return pruned


def _prune_primitive(value: Any, schema: dict[str, Any]) -> Any:
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        if value in enum:
            return value
        return enum[0]
    schema_type = schema.get("type")
    if schema_type == "string":
        return value if isinstance(value, str) else _synthesize_primitive(schema)
    if schema_type == "integer":
        return value if isinstance(value, int) and not isinstance(value, bool) else 1
    if schema_type == "number":
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else 1
    if schema_type == "boolean":
        return value if isinstance(value, bool) else True
    return value


def _synthesize_from_schema(schema: dict[str, Any]) -> Any:
    kind = _schema_kind(schema)
    if kind == "object":
        return _synthesize_object(schema)
    if kind == "array":
        return _synthesize_array(schema)
    return _synthesize_primitive(schema)


def _synthesize_object(schema: dict[str, Any]) -> dict[str, Any]:
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required = schema.get("required") or []
    result: dict[str, Any] = {}
    for key in required:
        child = props.get(key, {})
        result[key] = _synthesize_from_schema(child if isinstance(child, dict) else {})
    return result


def _synthesize_array(schema: dict[str, Any]) -> list[Any]:
    items_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
    min_items = schema.get("minItems")
    max_items = schema.get("maxItems")
    count = max(min_items if isinstance(min_items, int) else 1, 1)
    if isinstance(max_items, int) and count > max_items:
        count = max_items
    return [_synthesize_from_schema(items_schema) for _ in range(count)]


def _synthesize_primitive(schema: dict[str, Any]) -> Any:
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return enum[0]
    schema_type = schema.get("type")
    if schema_type == "string":
        return "示例"
    if schema_type == "integer":
        return 1
    if schema_type == "number":
        return 1
    if schema_type == "boolean":
        return True
    if isinstance(schema_type, list):
        for t in schema_type:
            if t == "string":
                return "示例"
            if t in ("integer", "number"):
                return 1
            if t == "boolean":
                return True
    return "示例"


def _collect_enum_values(schema: dict[str, Any], out: set[str]) -> None:
    if not isinstance(schema, dict):
        return
    enum = schema.get("enum")
    if isinstance(enum, list):
        for item in enum:
            if isinstance(item, str):
                out.add(item)
    props = schema.get("properties")
    if isinstance(props, dict):
        for child in props.values():
            if isinstance(child, dict):
                _collect_enum_values(child, out)
    items = schema.get("items")
    if isinstance(items, dict):
        _collect_enum_values(items, out)
    for key in ("allOf", "anyOf", "oneOf"):
        for sub in schema.get(key) or []:
            if isinstance(sub, dict):
                _collect_enum_values(sub, out)


def _shrink_strings(
    value: Any, *, max_chars: int, schema: dict[str, Any] | None = None
) -> Any:
    """按比例缩放字符串值，使 JSON blob 不超过 max_chars（保留结构与键名）。"""
    protected: set[str] = set()
    if schema is not None:
        _collect_enum_values(schema, protected)

    blob = json.dumps(value, ensure_ascii=False)
    if len(blob) <= max_chars:
        return value
    strings: list[tuple[Any, Any, str]] = []
    _collect_strings(value, strings)
    shrinkable = [(parent, key, s) for parent, key, s in strings if s not in protected]
    total_len = sum(len(s) for _, _, s in shrinkable)
    if total_len == 0:
        return value
    all_string_len = sum(len(s) for _, _, s in strings)
    structural = len(blob) - all_string_len
    protected_len = sum(len(s) for _, _, s in strings if s in protected)
    target_shrinkable = max(max_chars - structural - protected_len, 0)
    scale = target_shrinkable / total_len
    for parent, key, s in shrinkable:
        new_len = int(len(s) * scale)
        if new_len < len(s):
            parent[key] = s[:new_len]
    if len(json.dumps(value, ensure_ascii=False)) > max_chars:
        return _shrink_strings(value, max_chars=max_chars, schema=schema)
    return value


def _collect_strings(value: Any, out: list[tuple[Any, Any, str]]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, str):
                out.append((value, k, v))
            else:
                _collect_strings(v, out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            if isinstance(v, str):
                out.append((value, i, v))
            else:
                _collect_strings(v, out)
