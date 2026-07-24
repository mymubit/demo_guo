# -*- coding: utf-8 -*-
"""产物 payload JSON Schema 校验（无 LLM）。"""
from __future__ import annotations

from typing import Any

from apps.core.schema_validator import SchemaValidator
from apps.drama.services.skills_loader import SkillsBundleLoader, get_skills_loader


def validate_artifact_payload(artifact_key: str, payload: dict) -> list[str]:
    """返回错误列表；空列表表示通过。"""
    loader = get_skills_loader()
    try:
        schema_path = _resolve_artifact_schema_path(loader, artifact_key)
    except KeyError:
        return [f"未知产物: {artifact_key}"]

    validator = SchemaValidator(schema_root=loader.root)
    schema = validator.load_schema(schema_path)
    resolved = validator._resolve_path(schema_path)
    json_validator = validator._build_validator(schema, resolved)
    errors = sorted(json_validator.iter_errors(payload), key=lambda item: list(item.path))
    return [error.message for error in errors]


def _resolve_artifact_schema_path(loader: SkillsBundleLoader, artifact_key: str) -> str:
    """解析产物 schema 相对路径（相对 DRAMA_SKILLS_ROOT）。"""
    v5_contracts = loader._load_yaml("contracts/artifacts.yaml")
    v5_entry = (v5_contracts.get("artifacts") or {}).get(artifact_key)
    if isinstance(v5_entry, dict):
        schema_path = v5_entry.get("schema_path")
        if isinstance(schema_path, str) and schema_path.strip():
            return schema_path

    contract: dict[str, Any] = {}
    try:
        contract = loader.get_artifact_contract(artifact_key)
    except KeyError:
        pass

    path = contract.get("schema_path") or contract.get("schema")
    if isinstance(path, str) and path.strip():
        return path

    components = loader.v6_manifest.get("components") or {}
    component = components.get(artifact_key) or {}
    component_schema = component.get("schema")
    if isinstance(component_schema, str) and component_schema.strip():
        return component_schema

    raise KeyError(artifact_key)
