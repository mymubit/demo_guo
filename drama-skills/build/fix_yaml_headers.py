#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一 foundation/rules/*.yaml 首行注释为 v3.1 scope 术语。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "foundation" / "rules"
MAPPING = [
    ("# Tier1 ", "# global_core · "),
    ("# Tier2 ", "# genre_profile · "),
    ("# Tier3 ", "# stage_playbook · "),
    ("# Tier4 ", "# compliance_block · "),
]


def main() -> None:
    for path in ROOT.rglob("*.yaml"):
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or not lines[0].startswith("#"):
            continue
        header = lines[0]
        for old, new in MAPPING:
            if header.startswith(old):
                header = new + header[len(old) :]
                break
        header = (
            header.replace("SkillRuleItem.", "")
            .replace("同步至 section=", "section=")
            .replace("自 tier2-genre-rules 抽离", "自 genre_profile 长文抽离")
            .replace("题材 tier2 可覆盖", "题材 genre_profile 可覆盖")
        )
        if header != lines[0]:
            lines[0] = header
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
