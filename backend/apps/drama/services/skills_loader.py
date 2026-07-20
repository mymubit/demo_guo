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
from apps.drama.services.condition_eval import (
    evaluate_condition,
    module_enable_context,
)


def _discover_rule_files(root: Path) -> list[str]:
    """动态发现规则文件（根级 + genres/），避免硬编码清单与技能仓漂移。"""
    rules_dir = root / "foundation" / "rules"
    files = sorted(p for p in rules_dir.glob("*.yaml"))
    files += sorted(p for p in (rules_dir / "genres").glob("*.yaml"))
    return [str(p.relative_to(root)) for p in files]


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
        registry_roles = {
            role["agent_id"]: role for role in self.registry.get("roles", [])
        }
        phase_labels: dict[str, str] = {}
        for entry_type in ("original_track", "story_adapt"):
            for phase in self.get_orchestration_track(entry_type).get("phases", []):
                phase_labels.setdefault(
                    phase["phase"],
                    phase.get("label", phase["phase"]),
                )
        for stage in workbench.get("stages", []):
            role_id = stage.get("role")
            if role_id in role_outputs:
                artifact_key = role_outputs[role_id]
                stage["artifact"] = artifact_key
                stage["artifact_label"] = self.get_artifact_contract(artifact_key).get(
                    "label_zh", artifact_key
                )
            stage["label_zh"] = phase_labels.get(
                stage.get("orchestration_phase"),
                (registry_roles.get(role_id) or {}).get("name_zh", stage["id"]),
            )
            stage["role_label"] = (registry_roles.get(role_id) or {}).get(
                "name_zh", role_id
            )

        workbench["module_catalog"] = self.modules_catalog.get("modules", [])
        workbench["schema_version"] = "workbench-form.v1"
        workbench["skills_bundle_version"] = self.bundle_version
        workbench["theme_matrix"] = self._export_theme_matrix()
        return workbench

    def _export_theme_matrix(self) -> dict[str, Any]:
        """导出题材矩阵（含热门组合），供前端选题 UI 使用。"""
        raw = self.load_seed_yaml("foundation/theme-matrix.yaml")
        axes_src = raw.get("axes") or {}
        dim_order = raw.get("dim_order") or list(axes_src.keys())
        axes: dict[str, Any] = {}
        for key in dim_order:
            axis = axes_src.get(key) or {}
            axes[key] = {
                "label_zh": axis.get("label_zh", key),
                "hint": axis.get("hint"),
                "required": axis.get("min_select") == 1,
                "options": [
                    {
                        "value": opt.get("value"),
                        "label_zh": opt.get("label_zh", opt.get("value")),
                        "desc": opt.get("desc"),
                    }
                    for opt in (axis.get("options") or [])
                    if opt.get("value")
                ],
            }

        flavor = raw.get("flavor_tags") or {}

        def _axis_options(block: dict[str, Any]) -> list[dict[str, Any]]:
            return [
                {
                    "value": opt.get("value"),
                    "label_zh": opt.get("label_zh", opt.get("value")),
                    "desc": opt.get("desc"),
                }
                for opt in (block.get("options") or [])
                if opt.get("value")
            ]

        audience_channel = raw.get("audience_channel") or {}
        protagonist_structure = raw.get("protagonist_structure") or {}
        featured = []
        for combo in raw.get("featured_combos") or []:
            dims = combo.get("dims") or {}
            featured.append(
                {
                    "code": combo.get("id"),
                    "label_zh": combo.get("label_zh") or combo.get("label"),
                    "heat": combo.get("heat"),
                    "kind": "featured",
                    "emotion": dims.get("emotion"),
                    "identity": dims.get("identity"),
                    "conflict": dims.get("conflict"),
                    "world": dims.get("world"),
                    "flavor_tags": dims.get("flavor_tags") or combo.get("flavor_tags") or [],
                    "audience_channel": dims.get("audience_channel"),
                    "protagonist_structure": dims.get("protagonist_structure"),
                }
            )

        # preset_templates 使用 theme_code（非 code/id）；导出完整四轴供「常用题材」点选
        presets = []
        for item in raw.get("preset_templates") or []:
            dims = item.get("dims") or {}
            presets.append(
                {
                    "code": item.get("theme_code"),
                    "label_zh": item.get("label_zh") or item.get("label"),
                    "kind": "preset",
                    "emotion": dims.get("emotion"),
                    "identity": dims.get("identity"),
                    "conflict": dims.get("conflict"),
                    "world": dims.get("world"),
                    "flavor_tags": dims.get("flavor_tags") or [],
                    "audience_channel": dims.get("audience_channel"),
                    "protagonist_structure": dims.get("protagonist_structure"),
                }
            )

        return {
            "dim_order": dim_order,
            "axes": axes,
            "flavor_tags": {
                "max_select": flavor.get("max_select", 5),
                "categories": flavor.get("categories") or [],
                "options": [
                    {
                        "value": opt.get("value"),
                        "label_zh": opt.get("label_zh", opt.get("value")),
                        "category": opt.get("category"),
                        "tier": opt.get("tier", "standard"),
                    }
                    for opt in (flavor.get("options") or [])
                    if opt.get("value")
                ],
            },
            "featured_combos": featured,
            "preset_templates": presets,
            "axis_guidance": raw.get("axis_guidance") or {},
            "audience_channel": {
                "label_zh": audience_channel.get("label_zh", "受众频道"),
                "hint": audience_channel.get("hint"),
                "required": audience_channel.get("required", True),
                "default": audience_channel.get("default", "general"),
                "options": _axis_options(audience_channel),
            },
            "protagonist_structure": {
                "label_zh": protagonist_structure.get("label_zh", "主角结构"),
                "hint": protagonist_structure.get("hint"),
                "required": protagonist_structure.get("required", False),
                "options": _axis_options(protagonist_structure),
            },
        }

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

    def assemble_modules_for_role(
        self,
        agent_id: str,
        settings: dict[str, Any] | None = None,
        *,
        as_index: bool = False,
        budget_max_chars: int | None = None,
    ) -> dict[str, Any]:
        """结构化加载角色模块；返回 text + included/skipped + truncated。"""
        contract = self.get_role_contract(agent_id)
        module_ids = list(contract.get("modules") or [])
        policy = contract.get("module_policy") or {}
        evaluate = bool(policy.get("evaluate_enable_when"))
        max_chars = (
            int(budget_max_chars)
            if budget_max_chars is not None
            else int(policy.get("max_chars") or 0)
        )
        catalog = self.modules_catalog.get("modules") or {}
        context = module_enable_context(settings) if evaluate else {}

        parts: list[str] = []
        included: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        used = 0
        truncated = False
        for module_id in module_ids:
            meta = catalog.get(module_id) or {}
            label = meta.get("label_zh") or module_id
            expr = meta.get("enable_when")
            base_item = {
                "id": module_id,
                "label_zh": label,
                "enable_when": expr,
            }
            if evaluate and expr:
                try:
                    if not evaluate_condition(str(expr), context):
                        skipped.append({**base_item, "chars": 0, "reason": "enable_when"})
                        continue
                except ValueError:
                    skipped.append({**base_item, "chars": 0, "reason": "enable_when"})
                    continue
            body = self.load_module(module_id)
            if not body:
                skipped.append({**base_item, "chars": 0, "reason": "missing"})
                continue
            if as_index:
                first_line = body.splitlines()[0].strip() if body else ""
                chunk = f"- `{module_id}`（{label}）: {first_line[:80]}"
                mode = "index"
            else:
                chunk = f"### {module_id}\n{body}"
                mode = "full"
            sep = "\n\n" if parts else ""
            piece = f"{sep}{chunk}"
            if max_chars > 0 and used + len(piece) > max_chars:
                remain = max_chars - used
                if remain >= 80:
                    cut = f"{sep}{chunk[: remain - 20]}…(模块预算截断)"
                    parts.append(cut)
                    included.append(
                        {
                            **base_item,
                            "chars": len(cut) - len(sep),
                            "mode": "truncated",
                        }
                    )
                    used += len(cut)
                else:
                    skipped.append({**base_item, "chars": len(body), "reason": "budget"})
                truncated = True
                break
            parts.append(piece)
            included.append({**base_item, "chars": len(chunk), "mode": mode})
            used += len(piece)
        return {
            "text": "".join(parts),
            "included": included,
            "skipped": skipped,
            "truncated": truncated,
            "max_chars": max_chars,
            "evaluate_enable_when": evaluate,
            "as_index": as_index,
        }

    def load_modules_for_role(
        self,
        agent_id: str,
        settings: dict[str, Any] | None = None,
        *,
        as_index: bool = False,
    ) -> str:
        """加载角色模块；尊重 module_policy.evaluate_enable_when；max_chars>0 时才截断。"""
        return self.assemble_modules_for_role(
            agent_id, settings, as_index=as_index
        )["text"]

    def load_anti_examples(self, agent_id: str, *, max_items: int = 6) -> str:
        """加载角色反例摘要，供 Prompt L3 注入。"""
        entry = self.get_role_entry(agent_id)
        skill_dir = entry.get("skill_dir") or f"roles/{agent_id.replace('.', '-')}"
        path = self.root / skill_dir / "anti-examples.yaml"
        if not path.exists():
            return ""
        data = self._load_yaml(str(path.relative_to(self.root)))
        examples = list(data.get("examples") or [])[:max_items]
        lines: list[str] = []
        for item in examples:
            title = item.get("title") or item.get("id") or "anti-example"
            bits = [f"- {title}"]
            forbid = item.get("forbid_fields") or []
            if forbid:
                bits.append(f"禁止字段: {', '.join(str(x) for x in forbid)}")
            require = item.get("require_nonempty") or []
            if require:
                bits.append(f"必填非空: {', '.join(str(x) for x in require)}")
            note = item.get("note")
            if note:
                bits.append(str(note))
            if item.get("bad") is not None:
                bits.append(f"错误形态: {json.dumps(item['bad'], ensure_ascii=False)}")
            if item.get("good") is not None:
                bits.append(f"正确形态: {json.dumps(item['good'], ensure_ascii=False)}")
            lines.append("；".join(bits))
        return "\n".join(lines)

    def assemble_knowledge_for_role(
        self,
        agent_id: str,
        settings: dict[str, Any] | None = None,
        *,
        max_chars: int = 0,
        as_index: bool = False,
    ) -> dict[str, Any]:
        """结构化知识注入；返回 text + included/skipped + truncated。"""
        settings = settings or {}
        entry = self.get_role_entry(agent_id)
        skill_dir = entry.get("skill_dir") or f"roles/{agent_id.replace('.', '-')}"
        skill_path = self.root / skill_dir / "SKILL.md"
        empty = {
            "text": "",
            "included": [],
            "skipped": [],
            "truncated": False,
            "max_chars": max_chars,
        }
        if not skill_path.exists():
            return empty
        text = skill_path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        refs = [str(r) for r in (fm.get("references") or []) if isinstance(r, str)]
        knowledge_refs = [
            r
            for r in refs
            if "/knowledge/" in r.replace("\\", "/") or r.startswith("../../knowledge/")
        ]
        platform = str(settings.get("target_platform") or "generic").strip().lower()
        world = (
            ((settings.get("genre_matrix") or {}) if isinstance(settings.get("genre_matrix"), dict) else {}).get(
                "world"
            )
        )
        ranked: list[tuple[int, Path]] = []
        seen: set[Path] = set()
        for ref in knowledge_refs:
            path = (self.root / skill_dir / ref).resolve()
            for score_boost, file_path in _expand_knowledge_ref_paths(
                path, settings=settings, platform=platform
            ):
                if file_path in seen:
                    continue
                seen.add(file_path)
                score = score_boost
                name = file_path.name.lower()
                if platform != "generic" and platform in name:
                    score += 3
                if world and str(world).lower() in name:
                    score += 2
                if "market" in file_path.parts or "formula" in name:
                    score += 1
                if "originality" in name and settings.get("entry_type") == "story_adapt":
                    score += 4
                if agent_id == "drama.compliance-guard":
                    if "tier4" in name or "compliance" in name:
                        score += 6
                    elif "originality" in name:
                        score += 3
                if agent_id == "drama.script-scorer":
                    if "s-class" in name or "scoring-preset" in name:
                        score += 6
                ranked.append((score, file_path))
        ranked.sort(key=lambda item: (-item[0], str(item[1])))

        def _rel(path: Path) -> str:
            try:
                return str(path.resolve().relative_to(self.root.resolve())).replace("\\", "/")
            except ValueError:
                return path.name

        def _piece(path: Path, body: str) -> tuple[str, str]:
            if as_index:
                first = body.splitlines()[0].strip() if body else ""
                return f"- `{path.name}`: {first[:120]}", "index"
            return f"### {path.name}\n{body}", "full"

        included: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        if max_chars <= 0:
            chunks: list[str] = []
            for _, path in ranked:
                body = path.read_text(encoding="utf-8").strip()
                chunk, mode = _piece(path, body)
                chunks.append(chunk)
                included.append(
                    {"path": _rel(path), "chars": len(chunk), "mode": mode}
                )
            return {
                "text": "\n\n".join(chunks),
                "included": included,
                "skipped": skipped,
                "truncated": False,
                "max_chars": max_chars,
            }

        chunks = []
        used = 0
        truncated = False
        for index, (_, path) in enumerate(ranked):
            body = path.read_text(encoding="utf-8").strip()
            if not as_index and index >= 3:
                skipped.append(
                    {
                        "path": _rel(path),
                        "chars": len(body),
                        "reason": "budget",
                        "mode": "full",
                    }
                )
                truncated = True
                continue
            if as_index:
                piece, mode = _piece(path, body)
            else:
                snippet = body[:800]
                piece = f"### {path.name}\n{snippet}"
                mode = "truncated" if len(snippet) < len(body) else "full"
            if used + len(piece) > max_chars:
                remain = max_chars - used
                if remain < 80:
                    skipped.append(
                        {
                            "path": _rel(path),
                            "chars": len(body),
                            "reason": "budget",
                            "mode": mode,
                        }
                    )
                    truncated = True
                    break
                piece = piece[: remain - 3] + "..."
                mode = "truncated"
                truncated = True
            chunks.append(piece)
            included.append({"path": _rel(path), "chars": len(piece), "mode": mode})
            used += len(piece)
            if used >= max_chars:
                truncated = True
                for _, rest in ranked[index + 1 :]:
                    rest_body = rest.read_text(encoding="utf-8").strip()
                    skipped.append(
                        {
                            "path": _rel(rest),
                            "chars": len(rest_body),
                            "reason": "budget",
                            "mode": "full",
                        }
                    )
                break
        return {
            "text": "\n\n".join(chunks),
            "included": included,
            "skipped": skipped,
            "truncated": truncated,
            "max_chars": max_chars,
        }

    def load_knowledge_for_role(
        self,
        agent_id: str,
        settings: dict[str, Any] | None = None,
        *,
        max_chars: int = 0,
    ) -> str:
        """按角色 references 与题材/平台注入知识；max_chars<=0 时全文注入。

        - 平台专属单文件：文件名含 douyin/kuaishou 等时需平台匹配
        - 知识目录 catalog.yaml：仅平台匹配且题材命中的公式文件注入；0 命中则整包不注入
        """
        return self.assemble_knowledge_for_role(
            agent_id, settings, max_chars=max_chars
        )["text"]

    def load_fewshots(self, agent_id: str, *, max_shots: int = 2) -> str:
        """加载人工审阅后的 fewshots.v1.yaml（若存在）。"""
        entry = self.get_role_entry(agent_id)
        skill_dir = entry.get("skill_dir") or f"roles/{agent_id.replace('.', '-')}"
        path = self.root / skill_dir / "fewshots.v1.yaml"
        if not path.exists():
            return ""
        data = self._load_yaml(str(path.relative_to(self.root)))
        shots = list(data.get("fewshots") or [])[:max_shots]
        if not shots:
            return ""
        lines = ["以下为审阅通过的 few-shot 示例（模仿字段形态，勿照抄剧情）："]
        for index, shot in enumerate(shots, 1):
            lines.append(
                f"{index}. input={json.dumps(shot.get('input') or {}, ensure_ascii=False)}"
            )
            lines.append(
                f"   output={json.dumps(shot.get('output') or {}, ensure_ascii=False)}"
            )
        return "\n".join(lines)

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

    def assemble_rules_for_role(
        self,
        agent_id: str,
        settings: dict[str, Any],
        *,
        max_chars: int = 0,
    ) -> dict[str, Any]:
        """结构化规则注入；返回 text + sections + item_count + truncated。"""
        contract = self.get_role_contract(agent_id)
        rule_policy = contract.get("rule_policy") or {}
        scopes = rule_policy.get("scopes", ["global_core"])
        allowed_sections = [
            str(s) for s in (rule_policy.get("sections") or []) if str(s).strip()
        ]
        theme_code = _resolve_theme_code(settings, root=self.root)
        items: list[tuple[int, int, str, str]] = []

        for rel_path in _discover_rule_files(self.root):
            data = self._load_yaml(rel_path)
            tier = data.get("tier")
            for item in data.get("items", []):
                if not _rule_matches_scope(item, tier, scopes, agent_id, theme_code):
                    continue
                section = str(item.get("section") or "")
                if not _rule_matches_sections(section, allowed_sections, tier):
                    continue
                body = (item.get("body") or "").strip()
                if not body:
                    continue
                title = item.get("title", item.get("rule_key", ""))
                priority = int(item.get("priority", 100))
                pack_rank = _rule_pack_rank(agent_id, section, tier)
                items.append((pack_rank, priority, section, f"- {title}\n{body}"))

        items.sort(key=lambda row: (row[0], row[1]))
        text, truncated, used_sections, item_count = _join_rules_within_budget_meta(
            items, max_chars
        )
        return {
            "text": text,
            "sections_included": used_sections,
            "item_count": item_count,
            "truncated": truncated,
            "max_chars": max_chars,
        }

    def collect_rules(
        self,
        agent_id: str,
        settings: dict[str, Any],
        *,
        max_chars: int = 0,
    ) -> str:
        return self.assemble_rules_for_role(
            agent_id, settings, max_chars=max_chars
        )["text"]

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


# 知识文件名中的平台标记 → 仅当 target_platform 命中才注入
_KNOWLEDGE_PLATFORM_TOKENS: tuple[str, ...] = (
    "douyin",
    "kuaishou",
    "wechat",
    "bilibili",
    "xiaohongshu",
)


def _knowledge_platform_token(filename: str) -> str | None:
    """若文件名含平台标记则返回该标记，否则 None（视为通用知识）。"""
    name = filename.lower()
    for token in _KNOWLEDGE_PLATFORM_TOKENS:
        if token in name:
            return token
    return None


def _knowledge_platform_allows(filename: str, platform: str) -> bool:
    """平台专属知识：必须 target_platform 精确匹配（含别名归一）。"""
    token = _knowledge_platform_token(filename)
    if token is None:
        return True
    normalized = (platform or "generic").strip().lower()
    # wechat_miniprogram → wechat
    if normalized.startswith(token):
        return True
    if token == "wechat" and "wechat" in normalized:
        return True
    return normalized == token


def _genre_context(settings: dict[str, Any]) -> dict[str, Any]:
    """合并 settings 顶层与 genre_matrix 内的题材字段，供公式匹配。"""
    matrix = settings.get("genre_matrix") if isinstance(settings.get("genre_matrix"), dict) else {}
    flavor = settings.get("flavor_tags")
    if flavor is None:
        flavor = matrix.get("flavor_tags")
    if not isinstance(flavor, list):
        flavor = []
    return {
        "emotion": matrix.get("emotion") or settings.get("emotion"),
        "identity": matrix.get("identity") or settings.get("identity"),
        "conflict": matrix.get("conflict") or settings.get("conflict"),
        "world": matrix.get("world") or settings.get("world"),
        "audience_channel": (
            settings.get("audience_channel")
            or matrix.get("audience_channel")
            or "general"
        ),
        "protagonist_structure": (
            settings.get("protagonist_structure") or matrix.get("protagonist_structure")
        ),
        "flavor_tags": [str(x) for x in flavor],
    }


def _formula_clause_matches(clause: dict[str, Any], ctx: dict[str, Any]) -> bool:
    """单条 match 子句：所有出现的键都必须命中。"""
    for key, allowed in clause.items():
        if not isinstance(allowed, list) or not allowed:
            return False
        allowed_set = {str(x) for x in allowed}
        if key == "flavor_tags":
            tags = {str(x) for x in (ctx.get("flavor_tags") or [])}
            if tags.isdisjoint(allowed_set):
                return False
            continue
        value = ctx.get(key)
        if value is None or str(value) not in allowed_set:
            return False
    return True


def _expand_knowledge_catalog(
    catalog_path: Path,
    *,
    settings: dict[str, Any],
    platform: str,
) -> list[tuple[int, Path]]:
    """展开题材公式 catalog：平台不匹配或 0 命中 → 空（不注入 shared）。"""
    try:
        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict):
        return []
    required_platform = str(data.get("platform") or "").strip().lower()
    if required_platform and required_platform != (platform or "generic").strip().lower():
        return []
    ctx = _genre_context(settings)
    matched: list[tuple[int, Path]] = []
    for formula in data.get("formulas") or []:
        if not isinstance(formula, dict):
            continue
        rel = str(formula.get("file") or "").strip()
        if not rel:
            continue
        rules = formula.get("match_any") or []
        if not any(
            isinstance(rule, dict) and _formula_clause_matches(rule, ctx) for rule in rules
        ):
            continue
        file_path = (catalog_path.parent / rel).resolve()
        if file_path.is_file():
            matched.append((8, file_path))
    if not matched:
        return []
    shared_rel = str(data.get("shared") or "").strip()
    if shared_rel:
        shared_path = (catalog_path.parent / shared_rel).resolve()
        if shared_path.is_file():
            matched.insert(0, (9, shared_path))
    return matched


def _expand_knowledge_ref_paths(
    path: Path,
    *,
    settings: dict[str, Any],
    platform: str,
) -> list[tuple[int, Path]]:
    """普通知识文件 → 单路径；catalog.yaml / 含 catalog 的目录 → 题材匹配展开。"""
    if path.is_dir():
        catalog = path / "catalog.yaml"
        if catalog.is_file():
            return _expand_knowledge_catalog(catalog, settings=settings, platform=platform)
        return []
    if not path.is_file():
        return []
    if path.name == "catalog.yaml":
        return _expand_knowledge_catalog(path, settings=settings, platform=platform)
    if not _knowledge_platform_allows(path.name, platform):
        return []
    return [(0, path)]


def list_knowledge_catalog_files(catalog_path: Path) -> list[Path]:
    """库存展示用：列出 catalog 声明的全部公式文件（含 shared），不做题材过滤。"""
    try:
        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict):
        return []
    out: list[Path] = []
    shared_rel = str(data.get("shared") or "").strip()
    if shared_rel:
        shared = catalog_path.parent / shared_rel
        if shared.is_file():
            out.append(shared.resolve())
    for formula in data.get("formulas") or []:
        if not isinstance(formula, dict):
            continue
        rel = str(formula.get("file") or "").strip()
        if not rel:
            continue
        file_path = catalog_path.parent / rel
        if file_path.is_file():
            out.append(file_path.resolve())
    return out


def _parse_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        data = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


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


def _discover_genre_keys(root: Path) -> frozenset[str]:
    keys: set[str] = set()
    genres_dir = root / "foundation" / "rules" / "genres"
    if genres_dir.is_dir():
        for path in sorted(genres_dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            key = str(data.get("genre_key") or path.stem).strip()
            if key:
                keys.add(key)
    return frozenset(keys)


def _load_preset_theme_codes(root: Path) -> frozenset[str]:
    path = root / "foundation" / "theme-matrix.yaml"
    if not path.exists():
        return frozenset()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    codes: set[str] = set()
    for item in raw.get("preset_templates") or []:
        if not isinstance(item, dict):
            continue
        code = str(item.get("theme_code") or "").strip()
        if code:
            codes.add(code)
    return frozenset(codes)


_GENRE_MATRIX_AXES = ("emotion", "identity", "conflict", "world")


def _resolve_theme_code(settings: dict[str, Any], *, root: Path) -> str:
    """解析题材规则 scope_key：四轴走 matrix；预设须映射到已存在 genre 规则文件。"""
    matrix = settings.get("genre_matrix")
    if isinstance(matrix, dict) and all(
        str(matrix.get(axis) or "").strip() for axis in _GENRE_MATRIX_AXES
    ):
        return "matrix"

    preset = str(settings.get("preset_theme_code") or "").strip()
    genre_keys = _discover_genre_keys(root)
    if preset:
        if preset in genre_keys:
            return preset
        if preset in _load_preset_theme_codes(root) and "matrix" in genre_keys:
            return "matrix"
        raise ValueError(
            f"preset_theme_code={preset!r} 无法映射到已存在的题材规则文件；"
            f"可用 genre_key: {', '.join(sorted(genre_keys)) or '(无)'}"
        )

    raise ValueError(
        "缺少有效题材设定：请配置完整的 genre_matrix（emotion/identity/conflict/world）"
        "或 preset_theme_code（须映射到已存在的题材规则文件）"
    )


# compliance_block 在 role_policy.sections 中是元 section，对应 compliance-core 各子 section
_COMPLIANCE_ITEM_SECTIONS = frozenset(
    {
        "p0_categories",
        "p1_categories",
        "p2_advisories",
        "nine_dimension_risk_assessment",
        "justice_tail_rule",
        "values_bottom_line",
        "title_compliance_rules",
        "platform_specific",
        "three_phase_compliance_checklist",
        "fuse_behavior",
        "compliance_block",
    }
)


def _rule_matches_sections(
    section: str,
    allowed_sections: list[str],
    tier: int | None,
) -> bool:
    """未声明 sections 时保持全量 scope 行为；声明后按 section 收窄。"""
    if not allowed_sections:
        return True
    if section in allowed_sections:
        return True
    if "compliance_block" in allowed_sections and (
        tier == 4 or section in _COMPLIANCE_ITEM_SECTIONS
    ):
        return True
    return False


def _rule_pack_rank(agent_id: str, section: str, tier: int | None) -> int:
    """截断预算内优先保留本阶段 playbook，其次裁判/角色核心规则。"""
    # tier 3 = stage_playbook：任意角色最高优先，避免被 global 噪声挤掉
    if tier == 3:
        return 0
    if agent_id == "drama.compliance-guard":
        if tier == 4 or section in _COMPLIANCE_ITEM_SECTIONS:
            return 1
        if section == "originality_rules":
            return 2
        return 3
    if agent_id == "drama.script-scorer":
        if section == "scoring":
            return 1
        if section in {
            "continuity",
            "hook_effectiveness",
            "payment_checkpoint_3card",
            "character_rules",
            "episode_structure",
        }:
            return 2
        return 3
    return 1


def _join_rules_within_budget(
    items: list[tuple[int, int, str, str]],
    max_chars: int,
) -> str:
    """按完整规则块拼接；max_chars<=0 表示不截断。"""
    text, _truncated, _sections, _count = _join_rules_within_budget_meta(items, max_chars)
    return text


def _join_rules_within_budget_meta(
    items: list[tuple[int, int, str, str]],
    max_chars: int,
) -> tuple[str, bool, list[str], int]:
    """返回 (text, truncated, sections_included, item_count)。"""
    if max_chars <= 0:
        sections: list[str] = []
        for _pack, _prio, section, _text in items:
            if section and section not in sections:
                sections.append(section)
        return (
            "\n\n".join(text for _pack, _prio, _section, text in items),
            False,
            sections,
            len(items),
        )

    chunks: list[str] = []
    used = 0
    used_sections: list[str] = []
    item_count = 0
    truncated = False
    for _pack, _prio, section, text in items:
        sep = "\n\n" if chunks else ""
        piece = f"{sep}{text}"
        if used + len(piece) <= max_chars:
            chunks.append(piece)
            used += len(piece)
            item_count += 1
            if section and section not in used_sections:
                used_sections.append(section)
            continue
        remain = max_chars - used
        if remain >= 80:
            chunks.append(f"{sep}{text[: remain - 3]}...")
            item_count += 1
            if section and section not in used_sections:
                used_sections.append(section)
        truncated = True
        break
    return "".join(chunks), truncated, used_sections, item_count


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
        scope_key = str(item.get("scope_key") or "")
        return scope_key == theme_code
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
