#!/usr/bin/env python3
"""将工作台 YAML 导出为前端可直接消费的 JSON。"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict

import yaml

from lib.contracts_loader import (
    load_artifacts_contract,
    load_parameters_contract,
    role_output_artifacts,
)
from lib.parameter_resolver import resolve_enum, resolve_max_items
from lib.source_loader import load_source, normalize_options

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(relative_path: str) -> Dict[str, Any]:
    return yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8")) or {}


def merge_parameter_definition(
    field_name: str, field_def: Dict[str, Any], parameters: Dict[str, Any]
) -> Dict[str, Any]:
    param_ref = field_def.get("parameter_ref")
    if not param_ref:
        raise KeyError(f"工作台字段 {field_name} 缺少 parameter_ref")
    param = copy.deepcopy(parameters[param_ref])
    merged = {**param, **field_def}
    merged.pop("parameter_ref", None)
    if "source" in param:
        merged["options_source"] = param["source"]
    if "max_items_source" in param:
        merged["max_items_source"] = param["max_items_source"]
    if param_ref == "genre_matrix":
        merged["fields_source"] = param["source"]
    enum_values = resolve_enum(param, ROOT)
    if enum_values is not None:
        merged["enum"] = enum_values
    return merged


def export_definition() -> Dict[str, Any]:
    workbench = load_yaml("workbench/workbench.yaml")
    parameters = load_parameters_contract(ROOT).get("parameters") or {}
    output = copy.deepcopy(workbench)
    raw_fields = output["project_settings"]["fields"]
    resolved_fields: Dict[str, Any] = {}
    for name, definition in raw_fields.items():
        resolved_fields[name] = merge_parameter_definition(name, definition, parameters)
    output["project_settings"]["fields"] = resolved_fields

    for definition in resolved_fields.values():
        if "options_source" in definition:
            value = load_source(ROOT, definition.pop("options_source"))
            definition["options"] = normalize_options(value)
        if "fields_source" in definition:
            value = load_source(ROOT, definition.pop("fields_source"))
            definition["fields"] = {
                key: {
                    "label": axis.get("label_zh", key),
                    "required": axis.get("min_select") == 1,
                    "options": normalize_options(axis.get("options") or []),
                }
                for key, axis in value.items()
            }
        max_items = resolve_max_items(definition, ROOT)
        if "max_items_source" in definition:
            definition.pop("max_items_source")
        if max_items is not None:
            definition["max_items"] = max_items
        if definition.get("enum_items"):
            definition["items_enum"] = definition.pop("enum_items")
        if definition.get("items_type"):
            definition.setdefault("items", {"type": definition.pop("items_type")})
        for contract_only in (
            "enum_source",
            "source",
            "nullable",
            "unique_items",
            "max_items_source",
        ):
            definition.pop(contract_only, None)
    role_outputs = role_output_artifacts(load_artifacts_contract(ROOT))
    for stage in output.get("stages", []):
        role_id = stage.get("role")
        if role_id in role_outputs:
            stage["artifact"] = role_outputs[role_id]
    output["module_catalog"] = load_yaml("modules/catalog.yaml")["modules"]
    output["schema_version"] = "workbench-form.v1"
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="dist/workbench-form.v1.json",
        help="相对仓库根目录的输出路径",
    )
    args = parser.parse_args()
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(export_definition(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(output_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
