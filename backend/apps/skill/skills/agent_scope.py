# -*- coding: utf-8 -*-
"""drama.* Agent agent_id ↔ Tier3 scope 映射。

v3.1 stage_playbook 以 agent_id 作为 scope_key（见 foundation/rules/stage-playbook.yaml）。
"""
from __future__ import annotations

from typing import Optional


def node_scope_for_agent(agent_id: str) -> str:
    """返回 Tier3 规则 scope_key；drama.* 角色直接使用 agent_id。"""
    key = (agent_id or "").strip()
    if key.startswith("drama."):
        return key
    return ""


def genre_from_project_payload(project_payload: dict) -> str:
    theme = (project_payload or {}).get("theme") or ""
    return str(theme).strip()
