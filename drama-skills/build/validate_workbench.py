#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工作台、角色参数与后台配置策略一致性校验。"""
from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

from export_workbench_schema import export_definition
from lib.contracts_loader import (
    FORBIDDEN_ROLE_PARAM_KEYS,
    load_artifacts_contract,
    load_parameters_contract,
    parameter_names,
    producer_map,
    role_output_artifacts,
    role_parameter_refs,
)
from lib.parameter_resolver import resolve_enum

ROOT = Path(__file__).resolve().parents[1]
ERRORS: List[str] = []
FORBIDDEN_WORKBENCH_KEYS = FORBIDDEN_ROLE_PARAM_KEYS | {
    "type",
    "enum",
    "default",
    "items_type",
    "enum_items",
    "minimum",
    "maximum",
    "options_source",
    "fields_source",
    "max_items_source",
    "enum_source",
}


def load_yaml(relative_path: str) -> Dict[str, Any]:
    path = ROOT / relative_path
    if not path.exists():
        ERRORS.append(f"文件不存在: {relative_path}")
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        ERRORS.append(f"YAML 解析失败 {relative_path}: {exc}")
        return {}


def load_json(relative_path: str) -> Dict[str, Any]:
    path = ROOT / relative_path
    if not path.exists():
        ERRORS.append(f"文件不存在: {relative_path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        ERRORS.append(f"JSON 解析失败 {relative_path}: {exc}")
        return {}


def check_manifest() -> None:
    manifest = load_yaml("manifest/drama-skills.manifest.yaml")
    registry = load_yaml("registry.yaml")
    if manifest.get("bundle_version") != registry.get("version"):
        ERRORS.append("manifest.bundle_version 与 registry.version 不一致")
    path_groups = [
        manifest.get("registries") or {},
        manifest.get("workbench") or {},
        manifest.get("orchestration") or {},
        manifest.get("configuration_sources") or {},
        manifest.get("artifact_contracts") or {},
    ]
    for group in path_groups:
        for value in group.values():
            if isinstance(value, str) and not (ROOT / value).exists():
                ERRORS.append(f"manifest 引用不存在: {value}")
    contracts = (manifest.get("artifact_contracts") or {}).get("contracts")
    if contracts != "contracts/artifacts.yaml":
        ERRORS.append("manifest.artifact_contracts 必须指向 contracts/artifacts.yaml")
    if (manifest.get("artifact_contracts") or {}).get("schemas"):
        ERRORS.append("manifest.artifact_contracts 禁止内联 schemas map")
    workbench_manifest = manifest.get("workbench") or {}
    if workbench_manifest.get("parameters_contract") != "contracts/parameters.yaml":
        ERRORS.append("manifest.workbench.parameters_contract 必须指向 contracts/parameters.yaml")
    for key in (
        "parameters_schema_generator",
        "parameters_schema",
        "project_settings_schema",
    ):
        relative = workbench_manifest.get(key)
        if isinstance(relative, str) and not (ROOT / relative).exists():
            ERRORS.append(f"manifest 引用不存在: {relative}")


def check_config_policy() -> None:
    policy = load_yaml("manifest/config-policy.yaml")
    protected = policy.get("protected_paths") or []
    overlays = policy.get("overlay_files") or {}
    for relative_path, definition in overlays.items():
        if not (ROOT / relative_path).exists():
            ERRORS.append(f"overlay 文件不存在: {relative_path}")
        if any(fnmatch.fnmatch(relative_path, pattern) for pattern in protected):
            ERRORS.append(f"overlay 文件被 protected_paths 禁止: {relative_path}")
        if not (definition or {}).get("allowed_paths"):
            ERRORS.append(f"overlay 文件缺少 allowed_paths: {relative_path}")
    overlay_schema = load_json("schemas/ops-config-overlay.v1.schema.json")
    schema_files = set(
        (
            (
                ((overlay_schema.get("properties") or {}).get("overrides") or {})
                .get("properties")
            )
            or {}
        ).keys()
    )
    if set(overlays) != schema_files:
        ERRORS.append("ops overlay Schema 文件白名单与 config-policy 不一致")
    schema_required = set(
        (((overlay_schema.get("properties") or {}).get("audit") or {}).get("required"))
        or []
    )
    policy_required = set(
        ((policy.get("audit_requirements") or {}).get("required_fields")) or []
    )
    if schema_required != policy_required:
        ERRORS.append("ops overlay 审计必填字段与 config-policy 不一致")


def check_role_params() -> None:
    registry = load_yaml("registry.yaml")
    params = parameter_names(load_parameters_contract(ROOT))
    for role in registry.get("roles", []) or []:
        role_path = f"{role['skill_dir']}/role.yaml"
        meta = load_yaml(role_path)
        contract = meta.get("input_contract") or {}
        if contract.get("params_schema"):
            ERRORS.append(f"{role['agent_id']}: 禁止内联 params_schema")
        refs = contract.get("parameter_refs") or []
        expected = role_parameter_refs(role["agent_id"])
        if sorted(refs) != sorted(expected):
            ERRORS.append(f"{role['agent_id']}: parameter_refs 与 contracts 不一致")
        for param in refs:
            if param not in params:
                ERRORS.append(f"{role['agent_id']}: 引用未知参数 {param}")
        for mode_name, mode in (contract.get("input_modes") or {}).items():
            for field in ("required_params", "forbidden_params"):
                for param in (mode or {}).get(field) or []:
                    if param not in params:
                        ERRORS.append(
                            f"{role['agent_id']}.{mode_name}: {field} 引用未知参数 {param}"
                        )


def check_workbench() -> None:
    workbench = load_yaml("workbench/workbench.yaml")
    registry = load_yaml("registry.yaml")
    artifacts_contract = load_artifacts_contract(ROOT)
    producers = producer_map(artifacts_contract)
    role_map = {item["agent_id"]: item for item in registry.get("roles", []) or []}
    role_outputs = role_output_artifacts(artifacts_contract)
    params = load_parameters_contract(ROOT).get("parameters") or {}

    for stage in workbench.get("stages", []) or []:
        role_id = stage.get("role")
        if role_id not in role_map:
            ERRORS.append(f"工作台阶段 {stage.get('id')}: 未注册角色 {role_id}")
        elif stage.get("artifact"):
            ERRORS.append(f"工作台阶段 {stage.get('id')}: 禁止内联 artifact，由角色输出推导")
        elif producers.get(role_outputs.get(role_id)) != role_id:
            ERRORS.append(f"工作台阶段 {stage.get('id')}: 角色产物与 contracts producer 不一致")

    declared_main_phases = {
        stage.get("orchestration_phase")
        for stage in workbench.get("stages", []) or []
        if stage.get("stage_kind") == "main"
    }
    orchestration_phases = set()
    for track_path in (
        "orchestration/original-track.yaml",
        "orchestration/story-adapt-track.yaml",
    ):
        orchestration_phases.update(
            phase.get("phase")
            for phase in load_yaml(track_path).get("phases", []) or []
        )
    if declared_main_phases != orchestration_phases:
        ERRORS.append("工作台主阶段与编排 phases 不一致")

    fields = ((workbench.get("project_settings") or {}).get("fields") or {})
    matrix = load_yaml("foundation/theme-matrix.yaml")
    platforms = load_yaml("foundation/constraints/platform-profiles.yaml")
    presets = load_yaml("foundation/constraints/scoring-presets.yaml")
    if (params.get("target_platform") or {}).get("default") not in (
        platforms.get("platforms") or {}
    ):
        ERRORS.append("参数 target_platform 默认值未在 platform-profiles 注册")
    if (params.get("scoring_preset") or {}).get("default") not in (
        presets.get("presets") or {}
    ):
        ERRORS.append("参数 scoring_preset 默认值未注册")
    flavor_max = ((matrix.get("flavor_tags") or {}).get("max_select"))
    project_schema = load_json("schemas/project-settings.v1.schema.json")
    parameters_schema = load_json("schemas/generated/parameters.schema.json")
    parameter_defs = parameters_schema.get("$defs") or {}
    for field_name, definition in fields.items():
        for forbidden in FORBIDDEN_WORKBENCH_KEYS:
            if forbidden in (definition or {}):
                ERRORS.append(f"工作台字段 {field_name}: 禁止内联 {forbidden}")
        param_ref = (definition or {}).get("parameter_ref")
        if not param_ref:
            ERRORS.append(f"工作台字段 {field_name}: 缺少 parameter_ref")
        elif param_ref not in params:
            ERRORS.append(f"工作台字段 {field_name}: parameter_ref 未定义 {param_ref}")
        persist_path = (definition or {}).get("persist_path")
        if not persist_path:
            ERRORS.append(f"工作台字段 {field_name}: 缺少 persist_path")
        elif not schema_has_path(project_schema, persist_path, parameter_defs):
            ERRORS.append(f"工作台字段 {field_name}: persist_path 不存在 {persist_path}")
        for condition_key in ("visible_when", "required_when"):
            condition = (definition or {}).get(condition_key)
            if condition is not None and (
                not isinstance(condition, str) or "==" not in condition
            ):
                ERRORS.append(f"工作台字段 {field_name}: {condition_key} 语法不统一")
    schema_max = (parameter_defs.get("flavor_tags") or {}).get("maxItems")
    if flavor_max != schema_max:
        ERRORS.append("参数 Schema flavor_tags.maxItems 与 theme-matrix 不一致")

    entry_types = set(resolve_enum(params.get("entry_type") or {}, ROOT) or [])
    schema_entries = set((parameter_defs.get("entry_type") or {}).get("enum") or [])
    if entry_types != schema_entries:
        ERRORS.append("参数 Schema entry_type 与编排入口不一致")

    for path in workbench.get("derived_fields", []) or []:
        if not schema_has_path(project_schema, path, parameter_defs):
            ERRORS.append(f"derived_fields 路径不存在: {path}")
    for path in workbench.get("system_fields", []) or []:
        if not schema_has_path(project_schema, path, parameter_defs):
            ERRORS.append(f"system_fields 路径不存在: {path}")

    role_metas = {
        item["agent_id"]: load_yaml(f"{item['skill_dir']}/role.yaml")
        for item in registry.get("roles", []) or []
    }
    for target, projection in (workbench.get("runtime_projection") or {}).items():
        if target != "workflow" and target not in role_metas:
            ERRORS.append(f"runtime_projection 指向未注册角色: {target}")
            continue
        target_params = set(role_parameter_refs(target)) if target in role_metas else set()
        for param, source_path in (projection or {}).items():
            if param == "when":
                continue
            if target != "workflow" and param not in target_params:
                ERRORS.append(f"runtime_projection: {target}.{param} 未在角色参数注册")
            if not schema_has_path(project_schema, str(source_path), parameter_defs):
                ERRORS.append(f"runtime_projection 来源不存在: {source_path}")

    catalog = load_yaml("modules/catalog.yaml")
    panel = workbench.get("module_panel") or {}
    for module, meta in (catalog.get("modules") or {}).items():
        if (meta or {}).get("enable_when"):
            if panel.get("evaluate_enable_when") is not True:
                ERRORS.append(f"条件模块 {module}: 工作台未启用 enable_when")
            for role_id in (meta or {}).get("target_roles") or []:
                policy = (role_metas.get(role_id) or {}).get("module_policy") or {}
                if policy.get("evaluate_enable_when") is not True:
                    ERRORS.append(f"条件模块 {module}: 角色 {role_id} 未启用 enable_when")


def check_orchestration_contract() -> None:
    for relative_path in (
        "orchestration/original-track.yaml",
        "orchestration/story-adapt-track.yaml",
    ):
        data = load_yaml(relative_path)
        gates = data.get("gates") or {}
        for phase in data.get("phases", []) or []:
            gate = phase.get("approval_gate")
            if gate and gate not in gates:
                ERRORS.append(f"{relative_path}: phase 引用不存在的 gate {gate}")
        quality_loop = data.get("quality_loop") or {}
        if int(quality_loop.get("max_revision_rounds", 0)) <= 0:
            ERRORS.append(f"{relative_path}: 缺少有效 max_revision_rounds")
        conditions = (((quality_loop.get("on_fail") or {}).get("conditions") or {}).get("any"))
        if not conditions:
            ERRORS.append(f"{relative_path}: 质检失败条件未结构化")
        if "condition" in (quality_loop.get("on_fail") or {}):
            ERRORS.append(f"{relative_path}: 不得同时保留自然语言 condition")


def check_form_export() -> None:
    try:
        exported = export_definition()
        json.dumps(exported, ensure_ascii=False)
    except (KeyError, ValueError, OSError) as exc:
        ERRORS.append(f"工作台表单导出失败: {exc}")
        return
    fields = ((exported.get("project_settings") or {}).get("fields") or {})
    for name, definition in fields.items():
        if not definition.get("type"):
            ERRORS.append(f"工作台字段 {name}: 导出后缺少 type")
        unresolved = {
            key
            for key in ("options_source", "fields_source", "max_items_source", "parameter_ref")
            if key in definition
        }
        if unresolved:
            ERRORS.append(f"工作台字段 {name}: 导出后仍有未解析字段 {sorted(unresolved)}")
    for stage in exported.get("stages", []):
        if not stage.get("artifact") or not stage.get("label_zh"):
            ERRORS.append(f"工作台阶段 {stage.get('id')}: 导出后缺少产物或中文标签")


def resolve_schema_node(
    node: Dict[str, Any], parameter_defs: Dict[str, Any]
) -> Dict[str, Any]:
    ref = node.get("$ref")
    if not ref:
        return node
    marker = "generated/parameters.schema.json#/$defs/"
    if marker not in ref:
        return node
    param_name = ref.rsplit("/", 1)[-1]
    return parameter_defs.get(param_name) or {}


def schema_has_path(
    schema: Dict[str, Any],
    dotted_path: str,
    parameter_defs: Dict[str, Any],
) -> bool:
    current = schema
    for part in dotted_path.split("."):
        current = resolve_schema_node(current, parameter_defs)
        properties = current.get("properties") or {}
        if part not in properties:
            return False
        current = properties[part]
    return True


def check_generated_schemas() -> None:
    from lib.parameter_schema_generator import generated_artifacts

    for relative_path, expected in sorted(generated_artifacts(ROOT).items()):
        target = ROOT / relative_path
        if not target.exists():
            ERRORS.append(f"缺少生成物: {relative_path}")
            continue
        actual = target.read_text(encoding="utf-8")
        if actual != expected:
            ERRORS.append(f"生成物漂移: {relative_path}（请运行 python build/generate_parameter_schemas.py）")


def main() -> int:
    check_manifest()
    check_config_policy()
    check_role_params()
    check_generated_schemas()
    check_workbench()
    check_orchestration_contract()
    check_form_export()
    for message in ERRORS:
        print(f"ERROR {message}")
    print(f"\n工作台校验完成：{len(ERRORS)} 错误")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
