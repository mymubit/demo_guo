#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 registry.yaml 生成其余角色的 role.yaml 骨架（一次性工具）。"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry.yaml"
ROLES_DIR = ROOT / "roles"
SKIP = {"drama.script-writer"}


def main() -> None:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    for role in data.get("roles") or []:
        agent_id = role["agent_id"]
        if agent_id in SKIP:
            continue
        slug = agent_id.replace("drama.", "drama-")
        out_dir = ROLES_DIR / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "role.yaml"
        if out_path.exists():
            continue
        payload = {
            "agent_id": agent_id,
            "name": role.get("name"),
            "name_zh": role.get("name_zh"),
            "dept": role.get("dept"),
            "role_tier": role.get("role_tier"),
            "workspace_order": role.get("workspace_order"),
            "modules": role.get("modules") or [],
            "rule_policy": {
                "scopes": ["global_core", "genre_profile", "stage_playbook"],
                "max_chars": 2500,
            },
            "skill_dir": role.get("skill_dir"),
        }
        if role.get("role_tier") == "composite":
            payload["rule_policy"]["max_chars"] = 2800
        out_path.write_text(
            yaml.dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        print(f"created {out_path}")


if __name__ == "__main__":
    main()
