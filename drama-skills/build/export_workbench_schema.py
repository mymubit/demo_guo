#!/usr/bin/env python3
"""将工作台 YAML 导出为前端可直接消费的 JSON。"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict

import yaml

from lib.source_loader import load_source, normalize_options

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(relative_path: str) -> Dict[str, Any]:
    return yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8")) or {}


def export_definition() -> Dict[str, Any]:
    workbench = load_yaml("workbench/workbench.yaml")
    output = copy.deepcopy(workbench)
    fields = output["project_settings"]["fields"]
    for definition in fields.values():
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
        if "max_items_source" in definition:
            value = load_source(ROOT, definition.pop("max_items_source"))
            definition["max_items"] = value
        if definition.pop("enum_source", None) == "orchestration.*.entry_type":
            definition["enum"] = [
                load_yaml("orchestration/original-track.yaml")["entry_type"],
                load_yaml("orchestration/story-adapt-track.yaml")["entry_type"],
            ]
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
