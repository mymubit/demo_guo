#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将重组角色 SKILL.md 正文瘦身为索引文档（方法论在 foundation/modules/）。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from lib.contracts_loader import load_artifacts_contract, role_output_artifacts

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry.yaml"
ROLES_DIR = ROOT / "roles"
ROLE_OUTPUTS = role_output_artifacts(load_artifacts_contract(ROOT))

V31_NOTICE = (
    "> **v5.0**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。"
    "本文档仅保留 Cursor 触发方式与 I/O 索引。"
)

TRIGGERS: Dict[str, List[str]] = {
    "drama.topic-director": [
        "@drama-topic-director 我想写一部复仇×重生×职场的短剧",
    ],
    "drama.story-bible": [
        "@drama-story-bible 基于立项简报输出故事蓝图",
        "@drama-story-bible external_story=《...》 把这个故事改编成30集短剧蓝图",
    ],
    "drama.episode-designer": [
        "@drama-episode-designer episode_range=1-10",
    ],
    "drama.script-writer": [
        "@drama-script-writer 生成第1-5集正文",
        "@drama-script-writer episode_range=6-10",
    ],
    "drama.revision-master": [
        "@drama-revision-master episode_range=1-5 focus_areas=dialogue,format",
    ],
    "drama.script-scorer": [
        "@drama-script-scorer 评分第1-5集剧本",
    ],
    "drama.compliance-guard": [
        "@drama-compliance-guard 合规审查全剧剧本",
    ],
    "drama.delivery-tool": [
        "@drama-delivery-tool 输出宣发交付包",
    ],
}

EXTRA_READING: Dict[str, List[str]] = {
    "drama.topic-director": [
        "foundation/rules/philosophy.yaml",
        "knowledge/market/douyin-formulas.md",
        "knowledge/market/industry-benchmarks.md",
        "knowledge/market/market-insights.md",
    ],
    "drama.story-bible": [
        "foundation/rules/character-rules.yaml",
        "knowledge/quality/originality-rules.md",
        "knowledge/craft/shanyin-screenwriting-methodology.md",
    ],
    "drama.script-writer": [
        "foundation/constraints/script-format.yaml",
        "foundation/rules/philosophy.yaml",
        
    ],
    "drama.script-scorer": [
        "foundation/constraints/quality-scoring.yaml",
        "knowledge/quality/s-class-standards.md",
        "knowledge/quality/scoring-presets.md",
    ],
    "drama.revision-master": [
        "foundation/constraints/script-format.yaml",
    ],
    "drama.compliance-guard": [
        "knowledge/quality/tier4-compliance.md",
        "knowledge/quality/originality-rules.md",
    ],
}


def _split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def _rel_prefix(skill_dir: str) -> str:
    depth = skill_dir.count("/") + 1
    return "../" * depth


def _load_role_yaml(slug: str) -> Dict[str, Any]:
    path = ROLES_DIR / slug / "role.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _task_files(slug: str) -> List[str]:
    tasks_dir = ROLES_DIR / slug / "tasks"
    if not tasks_dir.is_dir():
        return []
    return sorted(p.name for p in tasks_dir.glob("*.md"))


def _build_io_table(role_meta: Dict[str, Any], registry_role: Dict[str, Any]) -> str:
    lines = ["| 方向 | 键 | 说明 |", "|------|-----|------|"]
    artifact = ROLE_OUTPUTS.get(registry_role.get("agent_id", ""), "")
    if artifact:
        lines.append(f"| 输出 | `{artifact}` | schema v1 |")

    required = (role_meta.get("input_contract") or {}).get("required_artifacts") or []
    optional = (role_meta.get("input_contract") or {}).get("optional_artifacts") or []
    params = (role_meta.get("input_contract") or {}).get("parameter_refs") or []

    for key in required:
        lines.append(f"| 输入（必填） | `{key}` | 上游产物 |")
    for key in optional:
        lines.append(f"| 输入（可选） | `{key}` | 上游产物 |")
    for key in params:
        lines.append(f"| 参数 | `{key}` | 运行参数 |")

    if len(lines) == 3 and not artifact:
        lines.append("| — | — | 见 role.yaml input_contract |")
    return "\n".join(lines)


def _build_body(registry_role: Dict[str, Any]) -> str:
    agent_id = registry_role["agent_id"]
    slug = agent_id.replace("drama.", "drama-")
    skill_dir = registry_role.get("skill_dir", "")
    prefix = _rel_prefix(skill_dir)
    role_meta = _load_role_yaml(slug)
    co_located = skill_dir.startswith("roles/")

    name_zh = registry_role.get("name_zh") or role_meta.get("name_zh") or slug
    role_line = role_meta.get("role") or role_meta.get("goal") or registry_role.get("description", "")
    if isinstance(role_line, str):
        role_line = role_line.strip().split("\n")[0]

    triggers = TRIGGERS.get(agent_id, [f"@{slug.replace('drama-', 'drama-')} 执行任务"])
    trigger_block = "\n".join(triggers)

    modules = registry_role.get("modules") or role_meta.get("modules") or []
    reading: List[str] = ["./role.yaml"] if co_located else [f"{prefix}roles/{slug}/role.yaml"]
    reading.extend(f"{prefix}{p}" for p in EXTRA_READING.get(agent_id, []))
    reading.extend(f"{prefix}modules/{m}.md" for m in modules)
    tasks = _task_files(slug)
    if co_located:
        reading.extend(f"./tasks/{t}" for t in tasks)
    else:
        reading.extend(f"{prefix}roles/{slug}/tasks/{t}" for t in tasks)

    dedup_reading: List[str] = []
    seen = set()
    for item in reading:
        if item not in seen:
            seen.add(item)
            dedup_reading.append(item)

    reading_lines = "\n".join(f"- `{p}`" for p in dedup_reading)
    io_table = _build_io_table(role_meta, registry_role)

    parts = [
        f"# {name_zh} v5.0",
        "",
        V31_NOTICE,
        f"> 角色配置 SSOT：`{'./role.yaml' if co_located else f'roles/{slug}/role.yaml'}`",
        "",
    ]
    if role_line:
        parts.extend([f"**职责**：{role_line}", ""])

    parts.extend(
        [
            "## 触发方式",
            "",
            "```",
            trigger_block,
            "```",
            "",
            "## 输入 / 输出",
            "",
            io_table,
            "",
            "## 延伸阅读",
            "",
            reading_lines,
            "",
        ]
    )

    includes = (role_meta.get("includes") or {}).get("foundation") or []
    if includes:
        parts.extend(
            [
                "## Foundation",
                "",
                "\n".join(f"- `{prefix}foundation/{inc}.yaml`" if inc.endswith((".yaml", ".yml")) else f"- `{prefix}foundation/{inc}.md`" for inc in includes),
                "",
            ]
        )

    return "\n".join(parts).rstrip() + "\n"


def slim_skill(skill_path: Path, registry_role: Dict[str, Any]) -> bool:
    text = skill_path.read_text(encoding="utf-8")
    fm_raw, _old_body = _split_frontmatter(text)
    if not fm_raw:
        return False

    meta = yaml.safe_load(fm_raw) or {}
    meta["version"] = "5.0.0"
    new_fm = yaml.dump(meta, allow_unicode=True, sort_keys=False).strip()
    new_body = _build_body(registry_role)
    skill_path.write_text(f"---\n{new_fm}\n---\n\n{new_body}", encoding="utf-8")
    return True


def main() -> None:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    slimmed = 0
    for role in data.get("roles") or []:
        skill_dir = role.get("skill_dir")
        if not skill_dir:
            continue
        skill_path = ROOT / skill_dir / "SKILL.md"
        if not skill_path.exists():
            print(f"SKIP missing: {skill_path}")
            continue
        if slim_skill(skill_path, role):
            slimmed += 1
            chars = len(skill_path.read_text(encoding="utf-8"))
            print(f"OK {role['agent_id']} ({chars} chars)")
    print(f"slimmed {slimmed} skills")


if __name__ == "__main__":
    main()
