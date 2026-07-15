#!/usr/bin/env python3
"""校验产物 Schema、合法样例与跨字段语义。"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

from lib.schema_validator import SchemaValidationError, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas" / "artifacts"
FIXTURE_PATH = ROOT / "build" / "fixtures" / "artifacts" / "valid-artifacts.json"
ERRORS: List[str] = []


def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def schema_registry() -> Dict[str, Path]:
    registry = load_yaml(ROOT / "registry.yaml")
    result: Dict[str, Path] = {}
    for role in registry.get("roles", []):
        version = role["schema_version"]
        result[version] = SCHEMA_ROOT / f"{version}.schema.json"
    return result


def validate_semantics(version: str, value: Dict[str, Any]) -> None:
    if version == "project-brief.v1":
        total = sum(value["rule_params"]["act_ratio"])
        if abs(total - 1.0) > 0.001:
            raise ValueError("act_ratio 权重和必须为 1")
    if version == "quality-report.v1":
        total = sum(
            item["weight"] for item in value["dimensions"].values()
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError("评分维度权重和必须为 1")
        weighted = sum(
            item["score"] * item["weight"]
            for item in value["dimensions"].values()
        )
        if abs(weighted - value["overall_score"]) > 1:
            raise ValueError("overall_score 与十维加权结果不一致")


def validate_invalid_cases(
    validator: SchemaValidator,
    schemas: Dict[str, Path],
    fixtures: Dict[str, Dict[str, Any]],
) -> None:
    for version, fixture in fixtures.items():
        schema = validator.load(schemas[version])
        required = schema.get("required") or []
        if not required:
            continue
        invalid = copy.deepcopy(fixture)
        invalid.pop(required[0], None)
        try:
            validator.validate(invalid, schema, current_file=schemas[version])
        except SchemaValidationError:
            continue
        ERRORS.append(f"{version}: 缺少必填字段的非法样例未被拒绝")


def main() -> int:
    validator = SchemaValidator(SCHEMA_ROOT)
    schemas = schema_registry()
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    for version, path in schemas.items():
        if not path.exists():
            ERRORS.append(f"缺少产物 Schema: {path.relative_to(ROOT)}")
            continue
        if version not in fixtures:
            ERRORS.append(f"缺少合法样例: {version}")
            continue
        try:
            validator.validate(
                fixtures[version],
                validator.load(path),
                current_file=path,
            )
            validate_semantics(version, fixtures[version])
        except (SchemaValidationError, ValueError) as exc:
            ERRORS.append(f"{version}: {exc}")
    validate_invalid_cases(validator, schemas, fixtures)

    for message in ERRORS:
        print(f"ERROR {message}")
    print(f"\n产物校验完成：{len(schemas)} Schema · {len(ERRORS)} 错误")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
