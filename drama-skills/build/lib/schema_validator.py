"""无第三方依赖的 JSON Schema 子集校验器。

仅实现本仓 Schema 使用的关键字；生产网站可替换为标准 JSON Schema 引擎。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class SchemaValidationError(ValueError):
    """Schema 校验失败。"""


class SchemaValidator:
    def __init__(self, schema_root: Path) -> None:
        self.schema_root = schema_root

    def load(self, path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _resolve_ref(self, ref_path: str, current_file: Optional[Path]) -> Dict[str, Any]:
        file_part, _, fragment = ref_path.partition("#")
        if file_part.startswith("#") or (not file_part and fragment):
            raise SchemaValidationError(f"暂不支持相对内部 $ref: {ref_path}")
        if file_part:
            target = self.schema_root / file_part
            resolved = self.load(target)
        elif current_file is not None:
            resolved = self.load(current_file)
        else:
            raise SchemaValidationError(f"无法解析 $ref: {ref_path}")
        if fragment:
            pointer = fragment if fragment.startswith("/") else f"/{fragment}"
            resolved = self._resolve_pointer(resolved, pointer)
        return resolved

    def _resolve_pointer(self, document: Any, pointer: str) -> Any:
        current = document
        if pointer in ("", "/"):
            return current
        for part in pointer.lstrip("/").split("/"):
            key = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(current, dict) or key not in current:
                raise SchemaValidationError(f"JSON Pointer 无效: {pointer}")
            current = current[key]
        return current

    def validate(
        self,
        instance: Any,
        schema: Dict[str, Any],
        path: str = "$",
        current_file: Optional[Path] = None,
    ) -> None:
        if "$ref" in schema:
            resolved = self._resolve_ref(schema["$ref"], current_file)
            target_file = None
            file_part = schema["$ref"].partition("#")[0]
            if file_part:
                target_file = self.schema_root / file_part
            self.validate(instance, resolved, path, target_file or current_file)
            return

        self._validate_compositions(instance, schema, path, current_file)
        self._validate_type(instance, schema, path)
        if "const" in schema and instance != schema["const"]:
            raise SchemaValidationError(f"{path}: 必须等于 {schema['const']!r}")
        if "enum" in schema and instance not in schema["enum"]:
            raise SchemaValidationError(f"{path}: 值不在枚举中")

        if isinstance(instance, dict):
            self._validate_object(instance, schema, path, current_file)
        elif isinstance(instance, list):
            self._validate_array(instance, schema, path, current_file)
        elif isinstance(instance, str):
            self._validate_string(instance, schema, path)
        elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
            self._validate_number(instance, schema, path)

    def _validate_compositions(
        self,
        instance: Any,
        schema: Dict[str, Any],
        path: str,
        current_file: Optional[Path],
    ) -> None:
        for child in schema.get("allOf", []):
            if "if" in child:
                if self._matches(instance, child["if"], current_file):
                    self.validate(instance, child.get("then", {}), path, current_file)
                elif "else" in child:
                    self.validate(instance, child["else"], path, current_file)
            else:
                self.validate(instance, child, path, current_file)
        if "anyOf" in schema and not any(
            self._matches(instance, child, current_file)
            for child in schema["anyOf"]
        ):
            raise SchemaValidationError(f"{path}: 不满足任一 anyOf 分支")
        if "oneOf" in schema:
            count = sum(
                self._matches(instance, child, current_file)
                for child in schema["oneOf"]
            )
            if count != 1:
                raise SchemaValidationError(f"{path}: 必须只满足一个 oneOf 分支")

    def _matches(
        self,
        instance: Any,
        schema: Dict[str, Any],
        current_file: Optional[Path],
    ) -> bool:
        try:
            self.validate(instance, schema, current_file=current_file)
            return True
        except SchemaValidationError:
            return False

    def _validate_type(
        self, instance: Any, schema: Dict[str, Any], path: str
    ) -> None:
        expected = schema.get("type")
        if expected is None:
            return
        types = expected if isinstance(expected, list) else [expected]
        checks = {
            "null": instance is None,
            "object": isinstance(instance, dict),
            "array": isinstance(instance, list),
            "string": isinstance(instance, str),
            "integer": isinstance(instance, int) and not isinstance(instance, bool),
            "number": isinstance(instance, (int, float))
            and not isinstance(instance, bool),
            "boolean": isinstance(instance, bool),
        }
        if not any(checks.get(item, False) for item in types):
            raise SchemaValidationError(f"{path}: 类型应为 {types}")

    def _validate_object(
        self,
        instance: Dict[str, Any],
        schema: Dict[str, Any],
        path: str,
        current_file: Optional[Path],
    ) -> None:
        for key in schema.get("required", []):
            if key not in instance:
                raise SchemaValidationError(f"{path}: 缺少必填字段 {key}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = set(instance) - set(properties)
            if extras:
                raise SchemaValidationError(f"{path}: 存在未知字段 {sorted(extras)}")
        for key, value in instance.items():
            if key in properties:
                self.validate(value, properties[key], f"{path}.{key}", current_file)

    def _validate_array(
        self,
        instance: List[Any],
        schema: Dict[str, Any],
        path: str,
        current_file: Optional[Path],
    ) -> None:
        if len(instance) < schema.get("minItems", 0):
            raise SchemaValidationError(f"{path}: 数组项不足")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            raise SchemaValidationError(f"{path}: 数组项过多")
        if schema.get("uniqueItems") and len({repr(item) for item in instance}) != len(
            instance
        ):
            raise SchemaValidationError(f"{path}: 数组项必须唯一")
        item_schema = schema.get("items")
        if item_schema:
            for index, value in enumerate(instance):
                self.validate(value, item_schema, f"{path}[{index}]", current_file)

    def _validate_string(
        self, instance: str, schema: Dict[str, Any], path: str
    ) -> None:
        if len(instance) < schema.get("minLength", 0):
            raise SchemaValidationError(f"{path}: 字符串过短")
        if "pattern" in schema and not re.match(schema["pattern"], instance):
            raise SchemaValidationError(f"{path}: 不匹配 pattern")

    def _validate_number(
        self, instance: float, schema: Dict[str, Any], path: str
    ) -> None:
        if "minimum" in schema and instance < schema["minimum"]:
            raise SchemaValidationError(f"{path}: 小于 minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            raise SchemaValidationError(f"{path}: 大于 maximum")
