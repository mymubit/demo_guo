#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Drama Skills 全库一致性校验。

检查项：
1. registry ↔ roles/*/role.yaml ↔ SKILL.md：目录存在、agent_id/产物/schema/modules 对齐
2. modules 引用的能力块文件存在，且无孤儿模块（未被任何角色挂载）
3. orchestration/*.yaml 引用的角色均已注册
4. stage-playbook 的 scope_key 均为有效 agent_id，且每个角色至少 1 条阶段规则
5. SKILL.md frontmatter references 路径可解析
6. 产物 DAG：所有 input_contract 消费的产物都有生产者（或在白名单：用户上传/运行参数）
7. 全库无已废弃角色名残留（历史文档除外）；无指向已删除规则文件的引用
8. agent-runtime.yaml 覆盖全部注册角色
9. 全库文本中的 knowledge/foundation/modules 相对路径引用均指向真实文件
10. knowledge/ 孤儿检测：每个知识长文必须被至少一处（SKILL/rules/modules/入口文档）引用
11. 角色↔Section 映射中的 section 必须在规则文件中真实存在

用法：python build/validate_skills.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
ERRORS: List[str] = []
WARNINGS: List[str] = []

# 用户上传或由外部提供的产物键（无库内生产者）
EXTERNAL_ARTIFACTS = {"external_script"}
# story_bible 分节兼容别名（v4 存量数据键，无独立生产者）
LEGACY_ALIAS_ARTIFACTS = {"character_bible", "series_outline"}

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

        for field in ("default_output_artifact_key", "schema_version", "dept"):
            if meta.get(field) != entry.get(field):
                err(
                    f"{agent_id}: {field} 不一致 registry={entry.get(field)} role.yaml={meta.get(field)}"
                )
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
            for ref in fm.get("references") or []:
                target = (skill_dir / ref).resolve()
                if not target.exists():
                    err(f"{agent_id}: SKILL.md reference 不存在 {ref}")

    for agent_id in registry.get("fast_track_agents", []):
        if agent_id not in agent_ids:
            err(f"fast_track_agents 含未注册角色 {agent_id}")

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
    produced = set()
    for meta in role_metas.values():
        produced.update((meta.get("output_contract") or {}).get("artifacts") or [])
    known = produced | EXTERNAL_ARTIFACTS | LEGACY_ALIAS_ARTIFACTS
    for agent_id, meta in role_metas.items():
        contract = meta.get("input_contract") or {}
        for group in ("required_artifacts", "required_artifacts_any_of", "optional_artifacts"):
            for key in contract.get(group) or []:
                if key not in known:
                    err(f"{agent_id}: 输入产物 {key} 没有任何生产者（{group}）")


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
    r"(?:knowledge|foundation|modules|orchestration|roles|inspirations)"
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
    mounted = set()
    for meta in role_metas.values():
        mounted.update(meta.get("modules") or [])
    for module_file in sorted((ROOT / "modules").glob("*.md")):
        if module_file.stem not in mounted:
            err(f"孤儿模块（未被任何角色挂载）: modules/{module_file.name}")


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
    check_orchestration(agent_ids)
    check_stage_playbook(agent_ids)
    check_artifact_dag(role_metas)
    check_agent_runtime(agent_ids)
    check_deprecated_tokens()
    check_path_references()
    check_knowledge_orphans()
    check_module_orphans(role_metas)
    check_section_mapping()

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
