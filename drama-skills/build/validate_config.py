#!/usr/bin/env python3
"""配置覆盖、条件表达式、项目派生与投影回归校验。"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

from lib.condition_eval import evaluate
from lib.config_resolver import ConfigResolver, OverlayPolicyError
from lib.schema_validator import SchemaValidationError, SchemaValidator
from synthesize_matrix_params import resolve_from_matrix

ROOT = Path(__file__).resolve().parents[1]
ERRORS: List[str] = []


def load_yaml(relative_path: str) -> Dict[str, Any]:
    return yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8")) or {}


def main() -> int:
    policy = load_yaml("manifest/config-policy.yaml")
    overlay = load_yaml("build/fixtures/config/overlay.yaml")
    project = json.loads(
        (ROOT / "build/fixtures/config/project-settings.json").read_text(
            encoding="utf-8"
        )
    )
    validator = SchemaValidator(ROOT / "schemas")
    try:
        validator.validate(
            project,
            validator.load(ROOT / "schemas/project-settings.v1.schema.json"),
        )
        validator.validate(
            overlay,
            validator.load(ROOT / "schemas/ops-config-overlay.v1.schema.json"),
        )
    except SchemaValidationError as exc:
        ERRORS.append(str(exc))

    seed_files = {
        path: load_yaml(path) for path in (policy.get("overlay_files") or {})
    }
    resolver = ConfigResolver(policy)
    try:
        resolved = resolver.apply_overlay(seed_files, overlay)
        quality = resolved["foundation/constraints/quality-scoring.yaml"]
        if quality["grade_thresholds"]["B"] != 78:
            ERRORS.append("运营覆盖未生效")
    except OverlayPolicyError as exc:
        ERRORS.append(str(exc))

    illegal = copy.deepcopy(overlay)
    illegal["overrides"] = {"registry.yaml": {"version": "broken"}}
    try:
        resolver.apply_overlay(seed_files, illegal)
        ERRORS.append("越权覆盖 registry.yaml 未被拒绝")
    except OverlayPolicyError:
        pass

    workbench = load_yaml("workbench/workbench.yaml")
    projection = resolver.project_runtime_params(
        project, workbench.get("runtime_projection") or {}
    )
    if projection.get("drama.script-writer", {}).get(
        "production_target_band"
    ) != "standard":
        ERRORS.append("项目设置未正确投影到正文官")
    if "drama.delivery-tool" not in projection:
        ERRORS.append("启用交付后未生成交付工具参数")

    context = copy.deepcopy(project)
    context["deliverables"] = project["creation_preferences"]["deliverables"]
    expressions: List[str] = []
    for definition in (
        (workbench.get("project_settings") or {}).get("fields") or {}
    ).values():
        for key in ("visible_when", "required_when"):
            if definition.get(key):
                expressions.append(definition[key])
    for definition in (load_yaml("modules/catalog.yaml").get("modules") or {}).values():
        if definition.get("enable_when"):
            expressions.append(definition["enable_when"])
    for expression in expressions:
        try:
            evaluate(expression, context)
        except ValueError as exc:
            ERRORS.append(str(exc))

    derived = resolve_from_matrix(
        {
            **project["genre_matrix"],
            "audience_channel": project.get("audience_channel", "general"),
            "protagonist_structure": project.get("protagonist_structure"),
            "flavor_tags": project.get("flavor_tags", []),
        }
    )
    if derived["matrix_key"] != project["derived"]["matrix_key"]:
        ERRORS.append(
            f"项目派生 matrix_key 与合成器不一致: "
            f"fixture={project['derived']['matrix_key']} synthesized={derived['matrix_key']}"
        )

    for message in ERRORS:
        print(f"ERROR {message}")
    print(f"\n配置校验完成：{len(ERRORS)} 错误")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
