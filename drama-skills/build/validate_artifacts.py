#!/usr/bin/env python3
"""校验产物 Schema、合法样例与跨字段语义。"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from lib.contracts_loader import load_artifacts_contract
from lib.schema_validator import SchemaValidationError, SchemaValidator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas" / "artifacts"
FIXTURE_PATH = ROOT / "build" / "fixtures" / "artifacts" / "valid-artifacts.json"
ERRORS: List[str] = []


def validate_semantics(artifact_key: str, value: Dict[str, Any]) -> None:
    if artifact_key == "project_brief":
        total = sum(value["rule_params"]["act_ratio"])
        if abs(total - 1.0) > 0.001:
            raise ValueError("act_ratio 权重和必须为 1")
    if artifact_key == "quality_report":
        total = sum(item["weight"] for item in value["dimensions"].values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError("评分维度权重和必须为 1")
        weighted = sum(
            item["score"] * item["weight"] for item in value["dimensions"].values()
        )
        if abs(weighted - value["overall_score"]) > 1:
            raise ValueError("overall_score 与十维加权结果不一致")


def validate_invalid_cases(
    validator: SchemaValidator,
    schemas: Dict[str, Path],
    fixtures: Dict[str, Dict[str, Any]],
) -> None:
    for artifact_key, fixture in fixtures.items():
        schema = validator.load(schemas[artifact_key])
        required = schema.get("required") or []
        if not required:
            continue
        invalid = copy.deepcopy(fixture)
        invalid.pop(required[0], None)
        try:
            validator.validate(invalid, schema, current_file=schemas[artifact_key])
        except SchemaValidationError:
            continue
        ERRORS.append(f"{artifact_key}: 缺少必填字段的非法样例未被拒绝")


def main() -> int:
    contract = load_artifacts_contract(ROOT)
    artifacts = contract.get("artifacts") or {}
    validator = SchemaValidator(SCHEMA_ROOT)
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    for artifact_key, definition in artifacts.items():
        schema_version = definition.get("schema_version")
        if not isinstance(schema_version, int) or schema_version < 1:
            ERRORS.append(f"{artifact_key}: schema_version 必须是正整数")
            continue
        schema_path = ROOT / definition["schema_path"]
        if not schema_path.exists():
            ERRORS.append(f"{artifact_key}: schema 路径不存在 {definition['schema_path']}")
            continue
        if artifact_key in fixtures:
            try:
                validator.validate(
                    fixtures[artifact_key],
                    validator.load(schema_path),
                    current_file=schema_path,
                )
                validate_semantics(artifact_key, fixtures[artifact_key])
            except (SchemaValidationError, ValueError) as exc:
                ERRORS.append(f"{artifact_key}: {exc}")
        elif definition.get("producer"):
            ERRORS.append(f"{artifact_key}: 缺少合法样例")

    schemas = {
        key: ROOT / definition["schema_path"]
        for key, definition in artifacts.items()
        if (ROOT / definition["schema_path"]).exists()
    }
    validate_invalid_cases(validator, schemas, fixtures)

    for message in ERRORS:
        print(f"ERROR {message}")
    print(f"\n产物校验完成：{len(artifacts)} 契约 · {len(ERRORS)} 错误")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
