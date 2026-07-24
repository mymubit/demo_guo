# -*- coding: utf-8 -*-
"""LLM 产物统一落库管线：parse → normalize → schema → substance gate。

所有角色（工作台主链 / 外部评测评分官与合规官 / reprocess）必须经此入口。
禁止在角色服务内再抄一套解析逻辑。
"""
from __future__ import annotations

from typing import Any

from apps.core.exceptions import SCHEMA_VALIDATION_FAILED, BusinessException
from apps.core.schema_validator import SchemaValidator
from apps.drama.services.artifact_normalize import normalize_artifact
from apps.drama.services.json_parse import parse_llm_json
from apps.drama.services.substance_gates import run_substance_gate


def ingest_llm_artifact(
    *,
    content: str,
    artifact_key: str,
    settings: dict[str, Any] | None = None,
    schema_path: str,
    validator: SchemaValidator | None = None,
) -> dict[str, Any]:
    """将模型原文对齐为可落库产物。

    1. parse_llm_json — 抽 JSON / 轻量语法修复
    2. normalize_artifact — settings/matrix 合成补全（非字段 SSOT）
    3. SchemaValidator — JSON Schema 契约
    4. run_substance_gate — 按产物类型的实质门禁
    """
    settings = settings or {}
    payload = parse_llm_json(content)
    if not isinstance(payload, dict):
        raise BusinessException(
            SCHEMA_VALIDATION_FAILED,
            "模型输出不是 JSON 对象，无法落库",
            http_status=422,
        )
    payload = normalize_artifact(artifact_key, payload, settings)

    schema_validator = validator or SchemaValidator()
    try:
        schema_validator.validate_file(payload, schema_path)
    except BusinessException:
        raise
    except Exception as exc:
        raise BusinessException(
            SCHEMA_VALIDATION_FAILED,
            f"产物 Schema 校验失败（模型已返回内容，但结构不合规，未落库）: {exc}",
            http_status=422,
        ) from exc

    run_substance_gate(artifact_key, payload)
    return payload
