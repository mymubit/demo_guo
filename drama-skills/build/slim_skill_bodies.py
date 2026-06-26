#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 12 角色 SKILL.md 正文瘦身为 v3.1 索引文档（方法论在 foundation/modules/）。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry.yaml"
ROLES_DIR = ROOT / "roles"

V31_NOTICE = (
    "> **v3.1**：规则 SSOT 见 `foundation/rules/`；角色契约 SSOT 见 `./role.yaml`。"
    "本文档仅保留 Cursor 触发方式与 I/O 索引。"
)

TRIGGERS: Dict[str, List[str]] = {
    "drama.topic-planner": [
        "@drama-topic-planner 我想写一部复仇×重生×职场的短剧",
        "@drama-topic-planner [矩阵] 情感轴=复仇 身份轴=重生 冲突轴=家族 世界观=古代",
        "@drama-topic-planner [adapt] 将这本小说改编为短剧立项",
    ],
    "drama.market-analyst": [
        "@drama-market-analyst 分析当前都市复仇题材市场",
        "@drama-market-analyst 六维拉片：参考剧《XXX》",
    ],
    "drama.world-architect": [
        "@drama-world-architect 基于立项简报构建世界观",
    ],
    "drama.character-designer": [
        "@drama-character-designer 设计主角与核心配角人设",
    ],
    "drama.plot-architect": [
        "@drama-plot-architect 输出第1-20集分集大纲",
        "@drama-plot-architect episode_range=1-10",
    ],
    "drama.narrative-engineer": [
        "@drama-narrative-engineer 基于大纲输出叙事工程方案",
    ],
    "drama.script-writer": [
        "@drama-script-writer 生成第1-5集剧本",
        "@drama-script-writer episode_range=6-10",
    ],
    "drama.script-reviewer": [
        "@drama-script-reviewer 审查第1-5集剧本",
    ],
    "drama.quality-reporter": [
        "@drama-quality-reporter 基于审稿报告输出质量报告",
    ],
    "drama.polish-master": [
        "@drama-polish-master 精修第1-5集剧本",
    ],
    "drama.production-pack": [
        "@drama-production-pack 输出制作发行包",
    ],
    "drama.compliance-guard": [
        "@drama-compliance-guard 合规审查全剧剧本",
    ],
}

EXTRA_READING: Dict[str, List[str]] = {
    "drama.topic-planner": [
        "foundation/methodology/cross-section.md",
        "knowledge/originality-rules.md",
    ],
    "drama.script-writer": [
        "foundation/constraints/script-format.yaml",
        "foundation/methodology/cross-section.md",
        "foundation/methodology/mckee-value-shift.md",
    ],
    "drama.script-reviewer": [
        "foundation/constraints/script-format.yaml",
    ],
    "drama.polish-master": [
        "foundation/constraints/script-format.yaml",
    ],
    "drama.compliance-guard": [
        "knowledge/tier4-compliance.md",
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
    artifact = registry_role.get("default_output_artifact_key") or role_meta.get(
        "default_output_artifact_key", ""
    )
    schema = registry_role.get("schema_version") or role_meta.get("schema_version", "")
    if artifact:
        lines.append(f"| 输出 | `{artifact}` | schema: `{schema}` |")

    required = (role_meta.get("input_contract") or {}).get("required_artifacts") or []
    optional = (role_meta.get("input_contract") or {}).get("optional_artifacts") or []
    params = (role_meta.get("input_contract") or {}).get("params") or []

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
        f"# {name_zh} v3.1",
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
    meta["version"] = "3.1.0"
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
