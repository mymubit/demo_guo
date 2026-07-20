#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drama Skills 全库一致性校验。

检查项：
1. registry ↔ roles/*/role.yaml ↔ SKILL.md：目录存在、agent_id/产物/schema/modules 对齐
2. modules 引用的能力块文件存在，且全部登记于 modules/catalog.yaml
3. orchestration/*.yaml 引用的角色均已注册
4. stage-playbook 的 scope_key 均为有效 agent_id，且每个角色至少 1 条阶段规则
5. SKILL.md frontmatter references 路径可解析
6. 产物 DAG：所有 input_contract 消费的产物都有生产者（或在白名单：用户上传/运行参数）
7. 全库无已废弃角色名残留（历史文档除外）；无指向已删除规则文件的引用
8. agent-runtime.yaml 覆盖全部注册角色
9. 全库文本中的 knowledge/foundation/modules 相对路径引用均指向真实文件
10. knowledge/ 孤儿检测：每个知识长文必须被至少一处（SKILL/rules/modules/入口文档）引用
11. 角色↔Section 映射中的 section 必须在规则文件中真实存在
12. 原子规则 rule_key 唯一且字段完整；数值 SSOT 不反向指向 knowledge/modules
13. 十维评分预设完整、权重和为 1
14. 流式产物列表与 artifacts 定义一致

用法：python build/validate_skills.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

from lib.contracts_loader import (
    FORBIDDEN_ROLE_PARAM_KEYS,
    artifact_keys,
    load_artifacts_contract,
    load_parameters_contract,
    parameter_names,
    producer_map,
    role_output_artifacts,
    role_parameter_refs,
)

ROOT = Path(__file__).resolve().parents[1]
ERRORS: List[str] = []
WARNINGS: List[str] = []

# 用户上传或由外部提供的产物键（无库内生产者）
EXTERNAL_ARTIFACTS = {"external_script"}

# 已废弃角色名（v3/v4 时代），不允许出现在活跃文档中
DEPRECATED_TOKENS = [
    "drama.character-relations",
    "drama-character-relations",
    "drama.series-architect",
    "drama-series-architect",
    "topic-planner",
    "market-analyst",
    "world-architect",
    "character-designer",
    "plot-architect",
    "narrative-engineer",
    "polish-master",
    "script-reviewer",
    "quality-reporter",
    "hook-designer",
    "game-adapter",
    "ip-adapter",
    "rhythm-designer",
    "storyboard-director",
    "dialogue-expert",
]
# 历史记录文档允许保留旧名（用于沿革说明）
HISTORY_DOCS = {"EVOLUTION_LOG.md", "ROLE-DESIGN-ANALYSIS.md"}
SCAN_SUFFIXES = {".md", ".yaml", ".yml"}


def err(msg: str) -> None:
    ERRORS.append(msg)


def warn(msg: str) -> None:
    WARNINGS.append(msg)


# 已按 Agent Skills 规范升级的试点角色：强制校验 description/分区/反例文件
AGENT_SKILL_PILOT_ROLES = {
    "drama.topic-director",
    "drama.story-bible",
}


def _check_agent_skill_format(
    agent_id: str,
    skill_dir: Path,
    skill_md: Path,
    fm: Dict[str, Any],
    skill_text: str,
) -> None:
    """校验 Agent Skills 写法：何时用/不用、分区、反例文件。"""
    desc = str(fm.get("description") or "")
    require_strict = agent_id in AGENT_SKILL_PILOT_ROLES or (skill_dir / "anti-examples.yaml").exists()
    if not require_strict:
        if desc and ("何时用" not in desc or "何时不用" not in desc):
            warn(f"{agent_id}: description 建议写明「何时用 / 何时不用」")
        return

    if not desc:
        err(f"{agent_id}: SKILL.md frontmatter 缺少 description")
    else:
        if "何时用" not in desc:
            err(f"{agent_id}: description 须包含「何时用」")
        if "何时不用" not in desc:
            err(f"{agent_id}: description 须包含「何时不用」")
    for heading in ("## 职责边界", "## 输入/输出契约", "## 模块索引", "## 反例", "## 自检清单"):
        if heading not in skill_text:
            err(f"{agent_id}: SKILL.md 缺少分区 {heading}")
    if not (skill_dir / "anti-examples.yaml").exists():
        err(f"{agent_id}: 试点角色缺少 anti-examples.yaml")


def load_yaml(path: Path) -> Dict[str, Any]:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        err(f"YAML 解析失败 {path.relative_to(ROOT)}: {exc}")
        return {}


def frontmatter(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        err(f"frontmatter 解析失败 {path.relative_to(ROOT)}: {exc}")
        return {}


def check_registry_roles(registry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    role_metas: Dict[str, Dict[str, Any]] = {}
    dept_codes = {d["code"] for d in registry.get("departments", [])}
    agent_ids = {r["agent_id"] for r in registry.get("roles", [])}

    for entry in registry.get("roles", []):
        agent_id = entry["agent_id"]
        skill_dir = ROOT / entry["skill_dir"]
        if entry.get("dept") not in dept_codes:
            err(f"{agent_id}: dept={entry.get('dept')} 未在 departments 注册")
        if not skill_dir.is_dir():
            err(f"{agent_id}: skill_dir 不存在 {entry['skill_dir']}")
            continue
        role_yaml = skill_dir / "role.yaml"
        skill_md = skill_dir / "SKILL.md"
        if not role_yaml.exists():
            err(f"{agent_id}: 缺少 role.yaml")
            continue
        if not skill_md.exists():
            err(f"{agent_id}: 缺少 SKILL.md")
        meta = load_yaml(role_yaml)
        role_metas[agent_id] = meta

        for field in ("dept",):
            if meta.get(field) != entry.get(field):
                err(
                    f"{agent_id}: {field} 不一致 registry={entry.get(field)} role.yaml={meta.get(field)}"
                )
        if meta.get("output_artifact"):
            err(f"{agent_id}: output_artifact 由 registry/contracts 维护，禁止写入 role.yaml")
        if meta.get("agent_id") != agent_id:
            err(f"{agent_id}: role.yaml agent_id={meta.get('agent_id')}")

        reg_modules = entry.get("modules") or []
        role_modules = meta.get("modules") or []
        if sorted(reg_modules) != sorted(role_modules):
            err(f"{agent_id}: modules 不一致 registry={reg_modules} role.yaml={role_modules}")
        for module in role_modules:
            if not (ROOT / "modules" / f"{module}.md").exists():
                err(f"{agent_id}: module 文件缺失 modules/{module}.md")

        tasks = (meta.get("tasks") or {}).get("available") or []
        for task in tasks:
            if not (skill_dir / "tasks" / f"{task}.md").exists():
                err(f"{agent_id}: task 文件缺失 tasks/{task}.md")

        if skill_md.exists():
            fm = frontmatter(skill_md)
            if "modules" in fm and sorted(fm.get("modules") or []) != sorted(role_modules):
                err(
                    f"{agent_id}: SKILL.md modules 与 role.yaml 不一致 "
                    f"{fm.get('modules') or []} != {role_modules}"
                )
            for ref in fm.get("references") or []:
                target = (skill_dir / ref).resolve()
                if not target.exists():
                    err(f"{agent_id}: SKILL.md reference 不存在 {ref}")
            # SKILL 正文漂移检测：role.yaml 声明的每个参数必须在 SKILL.md 中被提及
            skill_text = skill_md.read_text(encoding="utf-8")
            for param in (meta.get("input_contract") or {}).get("parameter_refs") or []:
                if f"`{param}`" not in skill_text and param not in skill_text:
                    err(f"{agent_id}: SKILL.md 未提及参数 {param}（与 role.yaml 漂移）")
            _check_agent_skill_format(agent_id, skill_dir, skill_md, fm, skill_text)

        anti = skill_dir / "anti-examples.yaml"
        if anti.exists():
            data = load_yaml(anti)
            examples = data.get("examples") or []
            if not examples:
                err(f"{agent_id}: anti-examples.yaml 缺少 examples")
            for item in examples:
                if not item.get("id"):
                    err(f"{agent_id}: anti-examples 条目缺少 id")

        contract = meta.get("input_contract") or {}
        if "params" in contract:
            err(f"{agent_id}: input_contract.params 已废弃，只允许 parameter_refs")
        if "params_schema" in contract:
            err(f"{agent_id}: input_contract.params_schema 已废弃，改用 parameter_refs")
        if "required_artifacts_any_of" in contract:
            err(f"{agent_id}: required_artifacts_any_of 已废弃，统一使用虚拟产物")
        if meta.get("output_contract"):
            err(f"{agent_id}: output_contract 已废弃，改用 output_artifact")
        if meta.get("schema_version"):
            err(f"{agent_id}: schema_version 复合字符串已废弃")
        if meta.get("default_output_artifact_key"):
            err(f"{agent_id}: default_output_artifact_key 已废弃，改用 output_artifact")

    for tool in registry.get("tools", []):
        tool_dir = ROOT / tool["skill_dir"]
        if not (tool_dir / "SKILL.md").exists():
            err(f"tool {tool['id']}: 缺少 SKILL.md")

    return role_metas


def check_orchestration(agent_ids: set) -> None:
    files = sorted((ROOT / "orchestration").glob("*.yaml"))
    if not files:
        err("orchestration/ 下没有编排文件")
    for path in files:
        data = load_yaml(path)
        referenced: List[str] = []
        for phase in data.get("phases", []) or []:
            referenced.extend(phase.get("agents") or [])
        loop = data.get("quality_loop") or {}
        referenced.extend(loop.get("parallel_judges") or [])
        if isinstance(loop.get("on_fail"), dict) and loop["on_fail"].get("agent"):
            referenced.append(loop["on_fail"]["agent"])
        referenced.extend(data.get("optional_agents") or [])
        referenced.extend(data.get("recommended_agents") or [])
        for agent_id in referenced:
            if agent_id not in agent_ids:
                err(f"{path.name}: 引用未注册角色 {agent_id}")


def check_stage_playbook(agent_ids: set) -> None:
    data = load_yaml(ROOT / "foundation/rules/stage-playbook.yaml")
    covered = set()
    for item in data.get("items", []):
        key = item.get("scope_key")
        if item.get("scope_type") == "agent":
            if key not in agent_ids:
                err(f"stage-playbook: scope_key={key} 不是有效角色")
            covered.add(key)
    for agent_id in sorted(agent_ids - covered):
        warn(f"stage-playbook: 角色 {agent_id} 没有阶段规则条目")


def check_artifact_dag(role_metas: Dict[str, Dict[str, Any]]) -> None:
    contract = load_artifacts_contract(ROOT)
    produced = set(producer_map(contract).keys())
    known = artifact_keys(contract) | EXTERNAL_ARTIFACTS
    for agent_id, meta in role_metas.items():
        contract = meta.get("input_contract") or {}
        for group in ("required_artifacts", "optional_artifacts"):
            for key in contract.get(group) or []:
                if key not in known:
                    err(f"{agent_id}: 输入产物 {key} 没有任何生产者（{group}）")
        for mode_name, mode in (contract.get("input_modes") or {}).items():
            for group in ("required_artifacts", "optional_artifacts"):
                for key in (mode or {}).get(group) or []:
                    if key not in known:
                        err(
                            f"{agent_id}.{mode_name}: 输入产物 {key} "
                            f"没有任何生产者（{group}）"
                        )


def check_deprecated_tokens() -> None:
    pattern = re.compile("|".join(re.escape(t) for t in DEPRECATED_TOKENS))
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if path.name in HISTORY_DOCS or "build" in path.parts:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = pattern.search(line)
            if match:
                err(
                    f"废弃角色名残留 {path.relative_to(ROOT)}:{lineno} → {match.group(0)}"
                )


def check_agent_runtime(agent_ids: set) -> None:
    data = load_yaml(ROOT / "foundation/constraints/agent-runtime.yaml")
    runtime_ids = set((data.get("agents") or {}).keys())
    for missing in sorted(agent_ids - runtime_ids):
        err(f"agent-runtime.yaml 缺少角色运行参数 {missing}")
    for stale in sorted(runtime_ids - agent_ids):
        err(f"agent-runtime.yaml 存在未注册角色 {stale}")


# 全库文本中出现的相对路径引用（knowledge/foundation/modules/orchestration/roles）
PATH_REF_PATTERN = re.compile(
    r"(?:knowledge|foundation|modules|orchestration|roles|contracts|inspirations)"
    r"(?:/[A-Za-z0-9_.\-]+)+\.(?:md|yaml|yml)"
)


def check_path_references() -> None:
    """所有文档/规则中提到的库内相对路径必须真实存在。"""
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if path.name in HISTORY_DOCS or "build" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for match in PATH_REF_PATTERN.finditer(text):
            ref = match.group(0)
            if not (ROOT / ref).exists():
                err(f"路径引用失效 {path.relative_to(ROOT)} → {ref}")


def check_knowledge_orphans() -> None:
    """knowledge/ 下每个长文必须被库内至少一处引用（索引文件除外）。"""
    index_files = {"knowledge-sections.md", "output-schemas.md"}
    knowledge_files = [
        p for p in (ROOT / "knowledge").rglob("*.md") if p.name not in index_files
    ]
    corpus: List[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if "build" in path.parts:
            continue
        corpus.append(path.read_text(encoding="utf-8"))
    blob = "\n".join(corpus)
    for kfile in knowledge_files:
        rel = kfile.relative_to(ROOT).as_posix()
        # 引用计数需排除自引用（自身文件内出现的路径不算）
        self_text = kfile.read_text(encoding="utf-8")
        refs = blob.count(rel) - self_text.count(rel)
        if refs <= 0:
            err(f"knowledge 孤儿文件（无任何引用）: {rel}")


def check_module_orphans(role_metas: Dict[str, Dict[str, Any]]) -> None:
    """模块目录声明的 target_roles 必须与实际挂载完全一致。"""
    mounted_by: Dict[str, set] = {}
    for agent_id, role_meta in role_metas.items():
        for module in role_meta.get("modules") or []:
            mounted_by.setdefault(module, set()).add(agent_id)
    catalog = load_yaml(ROOT / "modules" / "catalog.yaml")
    entries = catalog.get("modules") or {}
    allowed_lifecycles = set(catalog.get("lifecycles") or [])
    allowed_kinds = set(catalog.get("kinds") or [])
    files = {path.stem for path in (ROOT / "modules").glob("*.md")}
    registered = set(entries)
    for missing in sorted(files - registered):
        err(f"模块未登记 modules/catalog.yaml: modules/{missing}.md")
    for stale in sorted(registered - files):
        err(f"模块目录登记了不存在的文件: modules/{stale}.md")
    for module, meta in entries.items():
        lifecycle = (meta or {}).get("lifecycle")
        kind = (meta or {}).get("kind")
        if lifecycle not in allowed_lifecycles:
            err(f"模块 {module}: 非法 lifecycle={lifecycle}")
        if kind not in allowed_kinds:
            err(f"模块 {module}: 非法 kind={kind}")
        declared_roles = set((meta or {}).get("target_roles") or [])
        actual_roles = mounted_by.get(module, set())
        if declared_roles != actual_roles:
            err(
                f"模块 {module}: target_roles 与实际挂载不一致 "
                f"{sorted(declared_roles)} != {sorted(actual_roles)}"
            )
        if lifecycle == "active" and not actual_roles:
            err(f"活动模块 {module}: 未挂载任何角色")


def check_atomic_rules() -> None:
    """原子规则键唯一，且可执行层不把 knowledge/modules 声明为 SSOT。"""
    seen: Dict[str, Path] = {}
    rules_dir = ROOT / "foundation" / "rules"
    paths = list(rules_dir.glob("*.yaml")) + list((rules_dir / "genres").glob("*.yaml"))
    for path in sorted(paths):
        for item in load_yaml(path).get("items", []) or []:
            if not isinstance(item, dict):
                err(f"{path.relative_to(ROOT)}: items 含非对象条目")
                continue
            for field in ("rule_key", "section", "title", "priority", "body"):
                if item.get(field) in (None, ""):
                    err(f"{path.relative_to(ROOT)}: 原子规则缺少 {field}")
            rule_key = str(item.get("rule_key") or "")
            if rule_key in seen:
                err(
                    f"rule_key 重复 {rule_key}: "
                    f"{seen[rule_key].relative_to(ROOT)} / {path.relative_to(ROOT)}"
                )
            seen[rule_key] = path
            body = str(item.get("body") or "")
            if re.search(r"SSOT:\s*(?:knowledge|modules|roles|orchestration)/", body):
                err(f"{path.relative_to(ROOT)}: {rule_key} 的 SSOT 层级倒置")
    reference_pattern = re.compile(r"`(t[1-4]\.[a-zA-Z0-9_.-]+)`")
    for module_path in sorted((ROOT / "modules").glob("*.md")):
        text = module_path.read_text(encoding="utf-8")
        for rule_key in reference_pattern.findall(text):
            if rule_key not in seen:
                err(f"{module_path.relative_to(ROOT)}: 引用不存在的 rule_key {rule_key}")


def check_scoring_presets() -> None:
    scoring = load_yaml(ROOT / "foundation" / "constraints" / "quality-scoring.yaml")
    expected = {item["key"] for item in scoring.get("dimensions", []) or []}
    dimension_total = sum(
        float(item.get("weight", 0)) for item in scoring.get("dimensions", []) or []
    )
    if abs(dimension_total - 1.0) > 1e-9:
        err(f"quality-scoring: 十维权重和={dimension_total}，应为 1")
    presets = load_yaml(ROOT / "foundation" / "constraints" / "scoring-presets.yaml")
    for preset_id, preset in (presets.get("presets") or {}).items():
        weights = (preset or {}).get("weights") or {}
        if set(weights) != expected:
            err(f"评分预设 {preset_id}: 维度与 quality-scoring 不一致")
        total = sum(float(value) for value in weights.values())
        if abs(total - 1.0) > 1e-9:
            err(f"评分预设 {preset_id}: 权重和={total}，应为 1")
        if (
            float((preset or {}).get("pass_threshold", 0))
            < float((scoring.get("grade_thresholds") or {}).get("B", 0))
            and (preset or {}).get("delivery_eligible") is not False
        ):
            err(f"评分预设 {preset_id}: 低于 B 级但仍允许交付")


def check_artifact_chunk_map() -> None:
    # v5.2：artifact-chunk-map.yaml 空壳指针已删除，直接读 contracts/artifacts.yaml
    legacy_pointer = ROOT / "foundation" / "constraints" / "artifact-chunk-map.yaml"
    if legacy_pointer.exists():
        err("artifact-chunk-map.yaml 已废弃，禁止重新引入（SSOT: contracts/artifacts.yaml）")
    contract = load_artifacts_contract(ROOT)
    artifacts = set((contract.get("artifacts") or {}).keys())
    for key in contract.get("array_artifact_keys") or []:
        if key not in artifacts:
            err(f"contracts/artifacts: array_artifact_keys 含未定义产物 {key}")
    valid_candidates = artifacts | EXTERNAL_ARTIFACTS
    for key, definition in (contract.get("virtual_artifacts") or {}).items():
        candidates = set((definition or {}).get("candidates") or [])
        if not candidates:
            err(f"contracts/artifacts: 虚拟产物 {key} 没有 candidates")
        for candidate in sorted(candidates - valid_candidates):
            err(f"contracts/artifacts: 虚拟产物 {key} 引用未知产物 {candidate}")


def check_artifacts_contract(registry: Dict[str, Any]) -> None:
    contract = load_artifacts_contract(ROOT)
    artifacts = contract.get("artifacts") or {}
    producers = producer_map(contract)
    role_outputs = role_output_artifacts(contract)
    registered_roles = {
        role["agent_id"] for role in registry.get("roles", []) or []
    }
    for artifact_key, definition in artifacts.items():
        if not isinstance(definition.get("schema_version"), int) or definition["schema_version"] < 1:
            err(f"contracts/artifacts: {artifact_key} schema_version 必须是正整数")
        schema_path = ROOT / definition.get("schema_path", "")
        if not schema_path.exists():
            err(f"contracts/artifacts: {artifact_key} schema 路径不存在 {definition.get('schema_path')}")
        producer = definition.get("producer")
        if producer and producers.get(artifact_key) != producer:
            err(f"contracts/artifacts: {artifact_key} producer 映射不一致")
        if producer and producer not in registered_roles:
            err(f"contracts/artifacts: {artifact_key} producer 未注册 {producer}")
    for agent_id in sorted(registered_roles):
        if agent_id not in role_outputs:
            err(f"contracts/artifacts: 角色 {agent_id} 没有唯一输出产物")
    for role in registry.get("roles", []) or []:
        if role.get("output_artifact"):
            err(f"registry {role['agent_id']}: 禁止复制 output_artifact")


def check_parameters_contract(
    registry: Dict[str, Any], role_metas: Dict[str, Dict[str, Any]]
) -> None:
    contract = load_parameters_contract(ROOT)
    params = parameter_names(contract)
    role_refs = contract.get("role_parameter_refs") or {}
    workbench = load_yaml(ROOT / "workbench" / "workbench.yaml")
    fields = ((workbench.get("project_settings") or {}).get("fields") or {})

    for agent_id, refs in role_refs.items():
        for param in refs:
            if param not in params:
                err(f"contracts/parameters: {agent_id} 引用未知参数 {param}")

    for agent_id, meta in role_metas.items():
        declared = set(role_refs.get(agent_id) or [])
        used = set((meta.get("input_contract") or {}).get("parameter_refs") or [])
        if declared != used:
            err(
                f"{agent_id}: parameter_refs 与 contracts/parameters 不一致 "
                f"{sorted(used)} != {sorted(declared)}"
            )
        contract_block = meta.get("input_contract") or {}
        for mode_name, mode in (contract_block.get("input_modes") or {}).items():
            for field in ("required_params", "forbidden_params"):
                for param in (mode or {}).get(field) or []:
                    if param not in params:
                        err(f"{agent_id}.{mode_name}: {field} 引用未知参数 {param}")

    for field_name, definition in fields.items():
        if not (definition or {}).get("parameter_ref"):
            err(f"工作台字段 {field_name}: 缺少 parameter_ref")
        for forbidden in FORBIDDEN_ROLE_PARAM_KEYS:
            if forbidden in (definition or {}):
                err(f"工作台字段 {field_name}: 禁止内联 {forbidden}")
        param_ref = (definition or {}).get("parameter_ref")
        if param_ref and param_ref not in params:
            err(f"工作台字段 {field_name}: parameter_ref={param_ref} 未定义")

    covered = set()
    for refs in role_refs.values():
        covered.update(refs)
    for definition in fields.values():
        param_ref = (definition or {}).get("parameter_ref")
        if param_ref:
            covered.add(param_ref)
    workbench_full = load_yaml(ROOT / "workbench" / "workbench.yaml")
    for projection in (workbench_full.get("runtime_projection") or {}).values():
        for key in (projection or {}):
            if key != "when":
                covered.add(key)
    for tool in (workbench_full.get("external_tools") or {}).values():
        covered.update(((tool or {}).get("runtime_params") or {}).keys())
    uncovered = sorted(params - covered)
    if uncovered:
        err(f"contracts/parameters: 未挂载参数 {uncovered}")

    for role in registry.get("roles", []) or []:
        if (
            role.get("schema_version")
            or role.get("default_output_artifact_key")
            or role.get("output_artifact")
        ):
            err(
                f"registry {role['agent_id']}: 禁止复制产物或 Schema 定义"
            )


def check_constraint_consistency() -> None:
    checkpoint = load_yaml(
        ROOT / "foundation" / "constraints" / "continuity-checkpoint.yaml"
    )
    required = set(checkpoint.get("required_fields") or [])
    optional = set(checkpoint.get("optional_fields") or [])
    schema_fields = set((checkpoint.get("schema") or {}).keys())
    if required - schema_fields:
        err(f"continuity-checkpoint: 必填字段无 schema {sorted(required - schema_fields)}")
    if optional - schema_fields:
        err(f"continuity-checkpoint: 可选字段无 schema {sorted(optional - schema_fields)}")
    if required & optional:
        err(f"continuity-checkpoint: 字段同时为必填和可选 {sorted(required & optional)}")

    matrix = load_yaml(ROOT / "foundation" / "theme-matrix.yaml")
    series_scale = load_yaml(ROOT / "foundation" / "constraints" / "series-scale.yaml")
    matrix_ratio = ((matrix.get("param_synthesis") or {}).get("base") or {}).get("act_ratio")
    if matrix_ratio != series_scale.get("base_ratios"):
        err("theme-matrix.param_synthesis.base.act_ratio 与 series-scale.base_ratios 不一致")

    production = load_yaml(
        ROOT / "foundation" / "constraints" / "production-feasibility.yaml"
    )
    for tag, definition in (production.get("tags") or {}).items():
        if float((definition or {}).get("weight", -1)) < 0:
            err(f"production-feasibility: {tag} 权重不能为负")
    bands = production.get("complexity_bands") or {}
    lean_max = ((bands.get("lean") or {}).get("max_score"))
    standard_min = ((bands.get("standard") or {}).get("min_score"))
    standard_max = ((bands.get("standard") or {}).get("max_score"))
    complex_min = ((bands.get("complex") or {}).get("min_score"))
    if None in (lean_max, standard_min, standard_max, complex_min):
        err("production-feasibility: 复杂度分级边界不完整")
    elif not (lean_max + 1 == standard_min and standard_max + 1 == complex_min):
        err("production-feasibility: 复杂度分级必须连续且不重叠")

    genre_files = {
        path.name for path in (ROOT / "foundation" / "rules" / "genres").glob("*.yaml")
    }
    if genre_files != {"matrix.yaml"}:
        err(f"最新态只允许 genres/matrix.yaml，当前={sorted(genre_files)}")


MODULE_REQUIRED_SECTIONS = ("## 目标", "## 输入", "## 引用规则", "## 输出", "## 执行步骤", "## 失败条件", "## 自检清单")


def check_module_structure() -> None:
    """模块七段结构完整性：每个模块必须具备统一契约段落。"""
    for path in sorted((ROOT / "modules").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        missing = [s for s in MODULE_REQUIRED_SECTIONS if s not in text]
        if missing:
            err(f"modules/{path.name}: 缺少段落 {missing}")


def check_section_mapping() -> None:
    """knowledge-sections.md 角色映射中的 section 必须在规则文件中真实存在。"""
    defined_sections = set()
    rules_dir = ROOT / "foundation" / "rules"
    for path in list(rules_dir.glob("*.yaml")) + list((rules_dir / "genres").glob("*.yaml")):
        data = load_yaml(path)
        for item in data.get("items", []) or []:
            if isinstance(item, dict) and item.get("section"):
                defined_sections.add(str(item["section"]))
    # 由 constraints 合成、不在规则文件中的 section
    synthesized = {"quantitative_constraints", "format_standard", "genre_rules"}
    mapping_path = ROOT / "knowledge" / "knowledge-sections.md"
    for line in mapping_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| drama."):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        for section in (s.strip() for s in cells[1].split(",")):
            if section and section not in defined_sections | synthesized:
                err(f"knowledge-sections.md: {cells[0]} 引用不存在的 section `{section}`")


def main() -> int:
    registry = load_yaml(ROOT / "registry.yaml")
    if not registry:
        print("registry.yaml 加载失败")
        return 1
    role_metas = check_registry_roles(registry)
    agent_ids = {r["agent_id"] for r in registry.get("roles", [])}
    check_artifacts_contract(registry)
    check_parameters_contract(registry, role_metas)
    check_orchestration(agent_ids)
    check_stage_playbook(agent_ids)
    check_artifact_dag(role_metas)
    check_agent_runtime(agent_ids)
    check_deprecated_tokens()
    check_path_references()
    check_knowledge_orphans()
    check_module_orphans(role_metas)
    check_module_structure()
    check_section_mapping()
    check_atomic_rules()
    check_scoring_presets()
    check_artifact_chunk_map()
    check_constraint_consistency()

    for msg in WARNINGS:
        print(f"WARN  {msg}")
    for msg in ERRORS:
        print(f"ERROR {msg}")
    print(
        f"\n校验完成：{len(registry.get('roles', []))} 角色 · "
        f"{len(ERRORS)} 错误 · {len(WARNINGS)} 警告"
    )
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
