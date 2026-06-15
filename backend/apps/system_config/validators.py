# -*- coding: utf-8 -*-
"""配置值类型与规则校验。"""
from __future__ import annotations

import re
from typing import Any

from rest_framework.exceptions import ValidationError

from .models import SystemConfigItem


def normalize_value(value_type: str, value: Any) -> Any:
    """按配置类型规整值，失败时抛出 DRF ValidationError。"""
    if value_type == SystemConfigItem.ValueType.STRING:
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            raise ValidationError("字符串配置不能使用对象或数组")
        return str(value)

    if value_type == SystemConfigItem.ValueType.INT:
        if isinstance(value, bool):
            raise ValidationError("整数配置不能使用布尔值")
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("整数配置值格式错误") from exc

    if value_type == SystemConfigItem.ValueType.FLOAT:
        if isinstance(value, bool):
            raise ValidationError("浮点配置不能使用布尔值")
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("浮点配置值格式错误") from exc

    if value_type == SystemConfigItem.ValueType.BOOL:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lower = value.strip().lower()
            if lower in ("1", "true", "yes", "on"):
                return True
            if lower in ("0", "false", "no", "off"):
                return False
        raise ValidationError("布尔配置值格式错误")

    if value_type == SystemConfigItem.ValueType.JSON:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValidationError("JSON 配置必须是对象")
        return value

    if value_type == SystemConfigItem.ValueType.ARRAY:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValidationError("数组配置必须是列表")
        return value

    raise ValidationError("不支持的配置类型")


def validate_schema(value: Any, schema: dict | None) -> None:
    """简化版 schema 校验，覆盖 min/max/enum/pattern/required_keys。"""
    if not schema:
        return

    if "enum" in schema and value not in schema.get("enum", []):
        raise ValidationError("配置值不在允许范围内")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "min" in schema and value < schema["min"]:
            raise ValidationError(f"配置值不能小于 {schema['min']}")
        if "max" in schema and value > schema["max"]:
            raise ValidationError(f"配置值不能大于 {schema['max']}")

    if isinstance(value, str):
        min_length = schema.get("min_length")
        max_length = schema.get("max_length")
        pattern = schema.get("pattern")
        if min_length is not None and len(value) < int(min_length):
            raise ValidationError(f"配置文本长度不能小于 {min_length}")
        if max_length is not None and len(value) > int(max_length):
            raise ValidationError(f"配置文本长度不能大于 {max_length}")
        if pattern and not re.match(str(pattern), value):
            raise ValidationError("配置文本格式不匹配")

    if isinstance(value, dict):
        required_keys = schema.get("required_keys") or []
        missing = [key for key in required_keys if key not in value]
        if missing:
            raise ValidationError(f"JSON 配置缺少必填键：{', '.join(missing)}")

    if isinstance(value, list):
        if "min_items" in schema and len(value) < int(schema["min_items"]):
            raise ValidationError(f"数组长度不能小于 {schema['min_items']}")
        if "max_items" in schema and len(value) > int(schema["max_items"]):
            raise ValidationError(f"数组长度不能大于 {schema['max_items']}")
