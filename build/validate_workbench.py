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

ROOT = Path(__file__).resolve().parents[1]
ERRORS: List[str] = []


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
    allowed_types = {"string", "integer", "number", "boolean", "array", "object"}
    for role in registry.get("roles", []) or []:
        role_path = f"{role['skill_dir']}/role.yaml"
        meta = load_yaml(role_path)
        contract = meta.get("input_contract") or {}
        params_schema = contract.get("params_schema") or {}
        for name, definition in params_schema.items():
            if (definition or {}).get("type") not in allowed_types:
                ERRORS.append(f"{role['agent_id']}.{name}: 非法参数类型")
        for mode_name, mode in (contract.get("input_modes") or {}).items():
            for field in ("required_params", "forbidden_params"):
                for param in (mode or {}).get(field) or []:
                    if param not in params_schema:
                        ERRORS.append(
                            f"{role['agent_id']}.{mode_name}: {field} 引用未知参数 {param}"
                        )


def check_workbench() -> None:
    workbench = load_yaml("workbench/workbench.yaml")
    registry = load_yaml("registry.yaml")
    role_map = {item["agent_id"]: item for item in registry.get("roles", []) or []}
    artifacts = {
        item["agent_id"]: item["default_output_artifact_key"]
        for item in registry.get("roles", []) or []
    }
    for stage in workbench.get("stages", []) or []:
        role_id = stage.get("role")
        if role_id not in role_map:
            ERRORS.append(f"工作台阶段 {stage.get('id')}: 未注册角色 {role_id}")
        elif stage.get("artifact") != artifacts[role_id]:
            ERRORS.append(f"工作台阶段 {stage.get('id')}: 产物与角色契约不一致")

    fields = ((workbench.get("project_settings") or {}).get("fields") or {})
    matrix = load_yaml("foundation/theme-matrix.yaml")
    platforms = load_yaml("foundation/constraints/platform-profiles.yaml")
    presets = load_yaml("foundation/constraints/scoring-presets.yaml")
    if (fields.get("target_platform") or {}).get("default") not in (
        platforms.get("platforms") or {}
    ):
        ERRORS.append("工作台 target_platform 默认值未在 platform-profiles 注册")
    if (fields.get("scoring_preset") or {}).get("default") not in (
        presets.get("presets") or {}
    ):
        ERRORS.append("工作台 scoring_preset 默认值未注册")
    flavor_max = ((matrix.get("flavor_tags") or {}).get("max_select"))
    project_schema = load_json("schemas/project-settings.v1.schema.json")
    for field_name, definition in fields.items():
        persist_path = (definition or {}).get("persist_path")
        if not persist_path:
            ERRORS.append(f"工作台字段 {field_name}: 缺少 persist_path")
        elif not schema_has_path(project_schema, persist_path):
            ERRORS.append(f"工作台字段 {field_name}: persist_path 不存在 {persist_path}")
        for condition_key in ("visible_when", "required_when"):
            condition = (definition or {}).get(condition_key)
            if condition is not None and (
                not isinstance(condition, str) or "==" not in condition
            ):
                ERRORS.append(f"工作台字段 {field_name}: {condition_key} 语法不统一")
    schema_max = (
        (project_schema.get("properties") or {}).get("flavor_tags") or {}
    ).get("maxItems")
    if flavor_max != schema_max:
        ERRORS.append("项目 Schema flavor_tags.maxItems 与 theme-matrix 不一致")

    entry_types = {
        load_yaml("orchestration/original-track.yaml").get("entry_type"),
        load_yaml("orchestration/story-adapt-track.yaml").get("entry_type"),
    }
    schema_entries = set(
        (((project_schema.get("properties") or {}).get("entry_type") or {}).get("enum"))
        or []
    )
    if entry_types != schema_entries:
        ERRORS.append("项目 Schema entry_type 与编排入口不一致")

    for path in workbench.get("derived_fields", []) or []:
        if not schema_has_path(project_schema, path):
            ERRORS.append(f"derived_fields 路径不存在: {path}")
    for path in workbench.get("system_fields", []) or []:
        if not schema_has_path(project_schema, path):
            ERRORS.append(f"system_fields 路径不存在: {path}")

    role_metas = {
        item["agent_id"]: load_yaml(f"{item['skill_dir']}/role.yaml")
        for item in registry.get("roles", []) or []
    }
    for target, projection in (workbench.get("runtime_projection") or {}).items():
        if target != "workflow" and target not in role_metas:
            ERRORS.append(f"runtime_projection 指向未注册角色: {target}")
            continue
        target_params = (
            set(
                (
                    (role_metas[target].get("input_contract") or {})
                    .get("params_schema", {})
                    .keys()
                )
            )
            if target in role_metas
            else set()
        )
        for param, source_path in (projection or {}).items():
            if param == "when":
                continue
            if target != "workflow" and param not in target_params:
                ERRORS.append(f"runtime_projection: {target}.{param} 未在角色参数注册")
            if not schema_has_path(project_schema, str(source_path)):
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


def schema_has_path(schema: Dict[str, Any], dotted_path: str) -> bool:
    current = schema
    for part in dotted_path.split("."):
        properties = current.get("properties") or {}
        if part not in properties:
            return False
        current = properties[part]
    return True


def main() -> int:
    check_manifest()
    check_config_policy()
    check_role_params()
    check_workbench()
    check_orchestration_contract()
    for message in ERRORS:
        print(f"ERROR {message}")
    print(f"\n工作台校验完成：{len(ERRORS)} 错误")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
