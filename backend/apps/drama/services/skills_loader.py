# -*- coding: utf-8 -*-
"""Drama Skills Bundle 加载器。"""
from __future__ import annotations

import copy
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from django.conf import settings

from apps.drama.services.parameter_resolver import (
    load_source,
    normalize_options,
    resolve_enum,
    resolve_max_items,
)


_RULE_FILES = [
    "foundation/rules/philosophy.yaml",
    "foundation/rules/narrative-craft.yaml",
    "foundation/rules/rhythm-rules.yaml",
    "foundation/rules/character-rules.yaml",
    "foundation/rules/dialogue-rules.yaml",
    "foundation/rules/writing-rules.yaml",
    "foundation/rules/plotting-rules.yaml",
    "foundation/rules/scoring-core.yaml",
    "foundation/rules/learned-rules.yaml",
    "foundation/rules/stage-playbook.yaml",
    "foundation/rules/compliance-core.yaml",
    "foundation/rules/originality-rules.yaml",
    "foundation/rules/concept-rules.yaml",
    "foundation/rules/structure-rules.yaml",
    "foundation/rules/world-rules.yaml",
    "foundation/rules/production-rules.yaml",
    "foundation/rules/genre-profile.yaml",
]


class SkillsBundleLoader:
    """从 DRAMA_SKILLS_ROOT 读取 manifest、编排与集中契约。"""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or settings.DRAMA_SKILLS_ROOT)

    @property
    def manifest(self) -> dict[str, Any]:
        return self._load_yaml("manifest/drama-skills.manifest.yaml")

    @property
    def registry(self) -> dict[str, Any]:
        rel = self.manifest.get("registries", {}).get("roles", "registry.yaml")
        return self._load_yaml(rel)

    @property
    def modules_catalog(self) -> dict[str, Any]:
        rel = self.manifest.get("registries", {}).get("modules", "modules/catalog.yaml")
        return self._load_yaml(rel)

    @property
    def workbench(self) -> dict[str, Any]:
        rel = self.manifest.get("workbench", {}).get("definition", "workbench/workbench.yaml")
        return self._load_yaml(rel)

    @property
    def config_policy(self) -> dict[str, Any]:
        return self._load_yaml("manifest/config-policy.yaml")

    @property
    def workflow_transitions(self) -> dict[str, Any]:
        path = self.manifest.get("orchestration", {}).get("transitions")
        return self._load_yaml(path) if path else {}

    @property
    def agent_runtime(self) -> dict[str, Any]:
        rel = self.manifest.get("configuration_sources", {}).get(
            "agent_runtime", "foundation/constraints/agent-runtime.yaml"
        )
        return self._load_yaml(rel)

    @property
    def bundle_version(self) -> str:
        return str(self.manifest.get("bundle_version", "5.0.0"))

    @property
    def artifacts_contract(self) -> dict[str, Any]:
        rel = self.manifest.get("artifact_contracts", {}).get(
            "contracts", "contracts/artifacts.yaml"
        )
        return self._load_yaml(rel)

    @property
    def parameters_contract(self) -> dict[str, Any]:
        rel = self.manifest.get("workbench", {}).get(
            "parameters_contract", "contracts/parameters.yaml"
        )
        return self._load_yaml(rel)

    @property
    def project_settings_schema_path(self) -> str:
        return self.manifest.get("workbench", {}).get(
            "project_settings_schema", "schemas/project-settings.v1.schema.json"
        )

    def get_role_entry(self, agent_id: str) -> dict[str, Any]:
        for role in self.registry.get("roles", []):
            if role.get("agent_id") == agent_id:
                return role
        raise KeyError(f"未注册角色: {agent_id}")

    def get_role_contract(self, agent_id: str) -> dict[str, Any]:
        entry = self.get_role_entry(agent_id)
        skill_dir = entry.get("skill_dir") or f"roles/{agent_id.replace('.', '-')}"
        return self._load_yaml(f"{skill_dir}/role.yaml")

    def get_artifact_contract(self, artifact_key: str) -> dict[str, Any]:
        contract = self.artifacts_contract
        artifacts = contract.get("artifacts") or {}
        if artifact_key in artifacts:
            return dict(artifacts[artifact_key])
        external = contract.get("external_artifacts") or {}
        if artifact_key in external:
            return dict(external[artifact_key])
        virtual = contract.get("virtual_artifacts") or {}
        if artifact_key in virtual:
            return dict(virtual[artifact_key])
        raise KeyError(f"未知产物契约: {artifact_key}")

    def get_output_artifact_by_role(self, role: str) -> str:
        for key, definition in (self.artifacts_contract.get("artifacts") or {}).items():
            if (definition or {}).get("producer") == role:
                return key
        raise KeyError(f"角色 {role} 无产出产物")

    def get_parameter_definition(self, param_name: str) -> dict[str, Any]:
        parameters = self.parameters_contract.get("parameters") or {}
        if param_name not in parameters:
            raise KeyError(f"未知参数: {param_name}")
        return dict(parameters[param_name])

    def get_role_parameter_refs(self, agent_id: str) -> list[str]:
        refs = (self.parameters_contract.get("role_parameter_refs") or {}).get(agent_id)
        if refs is None:
            raise KeyError(f"角色 {agent_id} 无参数引用")
        return list(refs)

    def artifact_schema_path(self, artifact_key: str) -> str:
        contract = self.get_artifact_contract(artifact_key)
        schema_path = contract.get("schema_path")
        if not schema_path:
            raise KeyError(f"产物 {artifact_key} 无 schema_path")
        return schema_path

    def artifact_schema_version(self, artifact_key: str) -> int:
        contract = self.get_artifact_contract(artifact_key)
        version = contract.get("schema_version")
        if not isinstance(version, int) or version < 1:
            raise ValueError(f"产物 {artifact_key} schema_version 无效")
        return version

    def load_artifact_schema(self, artifact_key: str) -> dict[str, Any]:
        return self.load_json(self.artifact_schema_path(artifact_key))

    def producer_artifact_map(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for key, definition in (self.artifacts_contract.get("artifacts") or {}).items():
            producer = (definition or {}).get("producer")
            if producer:
                result[producer] = key
        return result

    def export_workbench_form(self) -> dict[str, Any]:
        workbench = copy.deepcopy(self.workbench)
        parameters = self.parameters_contract.get("parameters") or {}
        raw_fields = workbench["project_settings"]["fields"]
        resolved_fields: dict[str, Any] = {}
        for name, definition in raw_fields.items():
            resolved_fields[name] = self._merge_parameter_definition(
                name, definition, parameters
            )
        workbench["project_settings"]["fields"] = resolved_fields

        for definition in resolved_fields.values():
            if "options_source" in definition:
                value = load_source(self.root, definition.pop("options_source"))
                definition["options"] = normalize_options(value)
            if "fields_source" in definition:
                value = load_source(self.root, definition.pop("fields_source"))
                definition["fields"] = {
                    key: {
                        "label": axis.get("label_zh", key),
                        "required": axis.get("min_select") == 1,
                        "options": normalize_options(axis.get("options") or []),
                    }
                    for key, axis in value.items()
                }
            max_items = resolve_max_items(definition, self.root)
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

        role_outputs = self.producer_artifact_map()
        for stage in workbench.get("stages", []):
            role_id = stage.get("role")
            if role_id in role_outputs:
                artifact_key = role_outputs[role_id]
                stage["artifact"] = artifact_key
                stage["artifact_label"] = self.get_artifact_contract(artifact_key).get(
                    "label_zh", artifact_key
                )

        workbench["module_catalog"] = self.modules_catalog.get("modules", [])
        workbench["schema_version"] = "workbench-form.v1"
        return workbench

    def project_runtime_projection(
        self,
        agent_id: str,
        settings: dict[str, Any],
        workflow_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        projection_cfg = (self.workbench.get("runtime_projection") or {}).get(agent_id, {})
        if not projection_cfg:
            return {}
        when_expr = projection_cfg.get("when")
        if when_expr and not _eval_when(when_expr, settings):
            return {}
        parameters = self.parameters_contract.get("parameters") or {}
        result: dict[str, Any] = {}
        for param, source_path in projection_cfg.items():
            if param == "when":
                continue
            if param not in parameters:
                continue
            value = _deep_get(settings, source_path)
            if value is not None:
                result[param] = value
        wf_projection = (self.workbench.get("runtime_projection") or {}).get("workflow", {})
        if workflow_state and wf_projection:
            for param, source_path in wf_projection.items():
                if param not in parameters:
                    continue
                if param not in result:
                    value = _deep_get(settings, source_path)
                    if value is not None:
                        result[param] = value
            result["batch_cursor"] = workflow_state.get("batch_cursor")
            result["revision_round"] = workflow_state.get("revision_round")
        return result

    def apply_parameter_defaults(self, settings: dict[str, Any]) -> dict[str, Any]:
        """按 parameters contract 填充缺失默认值，不信任调用方内联类型/默认。"""
        result = copy.deepcopy(settings)
        fields = (self.workbench.get("project_settings") or {}).get("fields") or {}
        for field_def in fields.values():
            param_ref = field_def.get("parameter_ref")
            if not param_ref:
                continue
            persist_path = field_def.get("persist_path", param_ref)
            if _deep_get(result, persist_path) is not None:
                continue
            param_def = self.get_parameter_definition(param_ref)
            if "default" in param_def:
                _deep_set(result, persist_path, param_def["default"])
        return result

    def load_skill(self, agent_id: str) -> str:
        entry = self.get_role_entry(agent_id)
        skill_dir = entry.get("skill_dir") or f"roles/{agent_id.replace('.', '-')}"
        path = self.root / skill_dir / "SKILL.md"
        if not path.exists():
            return ""
        text = path.read_text(encoding="utf-8")
        return _strip_frontmatter(text)

    def load_module(self, module_id: str) -> str:
        path = self.root / "modules" / f"{module_id}.md"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def load_modules_for_role(self, agent_id: str) -> str:
        contract = self.get_role_contract(agent_id)
        parts: list[str] = []
        for module_id in contract.get("modules", []):
            body = self.load_module(module_id)
            if body:
                parts.append(f"### {module_id}\n{body}")
        return "\n\n".join(parts)

    def load_knowledge_sections_index(self) -> str:
        path = self.root / "knowledge/knowledge-sections.md"
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def get_orchestration_track(self, entry_type: str) -> dict[str, Any]:
        orch = self.manifest.get("orchestration", {})
        rel = orch.get(entry_type) or orch.get("original_track")
        if not rel:
            raise FileNotFoundError(f"缺少编排轨道: {entry_type}")
        return self._load_yaml(rel)

    def collect_rules(
        self,
        agent_id: str,
        settings: dict[str, Any],
        *,
        max_chars: int = 3200,
    ) -> str:
        contract = self.get_role_contract(agent_id)
        scopes = (contract.get("rule_policy") or {}).get("scopes", ["global_core"])
        theme_code = _resolve_theme_code(settings)
        items: list[tuple[int, str]] = []

        for rel_path in _RULE_FILES:
            data = self._load_yaml(rel_path)
            tier = data.get("tier")
            for item in data.get("items", []):
                if not _rule_matches_scope(item, tier, scopes, agent_id, theme_code):
                    continue
                body = (item.get("body") or "").strip()
                if body:
                    title = item.get("title", item.get("rule_key", ""))
                    priority = int(item.get("priority", 100))
                    items.append((priority, f"- {title}\n{body}"))

        items.sort(key=lambda pair: pair[0])
        text = "\n\n".join(body for _, body in items)
        if len(text) > max_chars:
            return text[: max_chars - 3] + "..."
        return text

    def load_seed_yaml(self, relative_path: str) -> dict[str, Any]:
        return self._load_yaml(relative_path)

    def _merge_parameter_definition(
        self,
        field_name: str,
        field_def: dict[str, Any],
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
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
        enum_values = resolve_enum(param, self.root)
        if enum_values is not None:
            merged["enum"] = enum_values
        return merged

    def _load_yaml(self, relative_path: str) -> dict[str, Any]:
        path = self.root / relative_path
        if not path.exists():
            raise FileNotFoundError(f"技能文件不存在: {relative_path}")
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def load_json(self, relative_path: str) -> Any:
        path = self.root / relative_path
        return json.loads(path.read_text(encoding="utf-8"))


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        match = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
        if match:
            return text[match.end() :].strip()
    return text.strip()


def _deep_get(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _deep_set(data: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    current = data
    for part in parts[:-1]:
        nested = current.get(part)
        if not isinstance(nested, dict):
            nested = {}
            current[part] = nested
        current = nested
    current[parts[-1]] = value


def _resolve_theme_code(settings: dict[str, Any]) -> str:
    matrix = settings.get("genre_matrix") or {}
    if matrix:
        return "-".join(
            matrix.get(axis, "")
            for axis in ("emotion", "identity", "conflict", "world")
        )
    return settings.get("preset_theme_code") or ""


def _rule_matches_scope(
    item: dict[str, Any],
    tier: int | None,
    scopes: list[str],
    agent_id: str,
    theme_code: str,
) -> bool:
    if tier == 1 and "global_core" in scopes:
        if item.get("scope_type") == "agent":
            return item.get("scope_key") == agent_id
        return item.get("scope_type") in (None, "global")
    if tier == 2 and "genre_profile" in scopes:
        scope_key = item.get("scope_key", "")
        return scope_key in ("", theme_code) or not scope_key
    if tier == 3 and "stage_playbook" in scopes:
        return item.get("scope_key") == agent_id
    if tier == 4 and "compliance_block" in scopes:
        return True
    return False


def _eval_when(expression: str, settings: dict[str, Any]) -> bool:
    match = re.match(
        r"^creation_preferences\.(\w+)\s*==\s*(true|false)$",
        expression.strip(),
    )
    if match:
        field, raw = match.groups()
        prefs = settings.get("creation_preferences") or {}
        expected = raw == "true"
        return bool(prefs.get(field)) == expected
    match = re.match(
        r"^(\w+)\s*==\s*'([^']+)'$",
        expression.strip(),
    )
    if match:
        field, expected = match.groups()
        return str(settings.get(field)) == expected
    match = re.match(
        r"^enable_delivery\s*==\s*(true|false)$",
        expression.strip(),
    )
    if match:
        raw = match.group(1)
        prefs = settings.get("creation_preferences") or {}
        expected = raw == "true"
        return bool(prefs.get("enable_delivery")) == expected
    return True


@lru_cache(maxsize=1)
def get_skills_loader() -> SkillsBundleLoader:
    return SkillsBundleLoader()
