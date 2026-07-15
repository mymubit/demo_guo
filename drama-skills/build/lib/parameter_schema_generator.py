"""从 contracts/parameters.yaml 生成 JSON Schema 定义与 project-settings 外壳。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from lib.contracts_loader import load_parameters_contract
from lib.parameter_resolver import resolve_parameter_schema_fragment

ROOT = Path(__file__).resolve().parents[2]
PARAMETERS_SCHEMA_REL = "generated/parameters.schema.json"
PARAMETERS_REF_PREFIX = f"{PARAMETERS_SCHEMA_REL}#/$defs/"

NESTED_REQUIRED: Dict[str, List[str]] = {
    "creation_preferences": [
        "batch_episode_max",
        "outline_mode",
        "scoring_preset",
        "compliance_check_mode",
        "enable_delivery",
    ],
    "production_context": ["target_band"],
}

TOP_LEVEL_REQUIRED = [
    "schema_version",
    "entry_type",
    "episode_count",
    "target_platform",
    "production_context",
    "creation_preferences",
    "audit",
]


def load_workbench_fields(root: Path) -> Dict[str, Any]:
    workbench = yaml.safe_load((root / "workbench/workbench.yaml").read_text(encoding="utf-8")) or {}
    return ((workbench.get("project_settings") or {}).get("fields") or {})


def generate_parameters_schema(root: Optional[Path] = None) -> Dict[str, Any]:
    base = root or ROOT
    contract = load_parameters_contract(base)
    parameters = contract.get("parameters") or {}
    defs: Dict[str, Any] = {}
    for name in sorted(parameters):
        defs[name] = resolve_parameter_schema_fragment(name, parameters[name], base)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "drama-skills://schemas/generated/parameters",
        "title": "Drama Skills Parameter Definitions",
        "description": "由 contracts/parameters.yaml 生成；禁止手改。",
        "$defs": defs,
    }


def _param_ref(param_name: str) -> Dict[str, str]:
    return {"$ref": f"{PARAMETERS_REF_PREFIX}{param_name}"}


def _set_nested_property(
    properties: Dict[str, Any],
    persist_path: str,
    param_name: str,
) -> None:
    parts = persist_path.split(".")
    if len(parts) == 1:
        properties[parts[0]] = _param_ref(param_name)
        return
    parent, child = parts[0], parts[1]
    parent_schema = properties.setdefault(
        parent,
        {"type": "object", "properties": {}, "additionalProperties": False},
    )
    parent_props = parent_schema.setdefault("properties", {})
    parent_props[child] = _param_ref(param_name)
    if parent in NESTED_REQUIRED:
        parent_schema["required"] = list(NESTED_REQUIRED[parent])


def generate_project_settings_schema(root: Optional[Path] = None) -> Dict[str, Any]:
    base = root or ROOT
    fields = load_workbench_fields(base)
    properties: Dict[str, Any] = {
        "schema_version": {"const": "project-settings.v1"},
        "project_id": {"type": "string"},
        "skills_version": {"type": "string"},
        "skills_git_ref": {"type": "string"},
        "title": {"type": "string"},
        "platform_policy": {
            "type": "object",
            "properties": {
                "policy_version": {"type": ["string", "null"]},
                "policy_source": {"type": ["string", "null"]},
                "verified_at": {"type": ["string", "null"]},
            },
            "additionalProperties": False,
        },
        "derived": {
            "type": "object",
            "readOnly": True,
            "properties": {
                "matrix_key": {"type": "string"},
                "rule_params_ref": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "audit": {
            "type": "object",
            "required": ["revision", "updated_at", "updated_by"],
            "properties": {
                "revision": {"type": "integer", "minimum": 1},
                "created_at": {"type": "string"},
                "updated_at": {"type": "string"},
                "updated_by": {"type": "string"},
            },
            "additionalProperties": False,
        },
    }

    for field_name in sorted(fields):
        definition = fields[field_name] or {}
        param_name = definition.get("parameter_ref")
        persist_path = definition.get("persist_path")
        if not param_name or not persist_path:
            raise KeyError(f"工作台字段 {field_name} 缺少 parameter_ref 或 persist_path")
        _set_nested_property(properties, persist_path, param_name)

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "drama-skills://schemas/project-settings.v1",
        "title": "短剧项目设置",
        "type": "object",
        "required": TOP_LEVEL_REQUIRED,
        "properties": properties,
        "allOf": [
            {
                "if": {"properties": {"entry_type": {"const": "story_adapt"}}},
                "then": {"required": ["external_story"]},
            },
            {
                "if": {"properties": {"entry_type": {"const": "original_track"}}},
                "then": {"required": ["core_idea"]},
            },
        ],
        "additionalProperties": False,
    }


def stable_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def generated_artifacts(root: Optional[Path] = None) -> Dict[str, str]:
    base = root or ROOT
    return {
        f"schemas/{PARAMETERS_SCHEMA_REL}": stable_json(generate_parameters_schema(base)),
        "schemas/project-settings.v1.schema.json": stable_json(
            generate_project_settings_schema(base)
        ),
    }
