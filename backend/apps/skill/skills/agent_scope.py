# -*- coding: utf-8 -*-
"""drama.* Agent agent_id ↔ Tier3 scope 映射。

旧的 brief/structure/outline/script 等 node scope 已移除。
drama.* Agent 使用 dept code 作为 Tier3 scope。
"""
from __future__ import annotations

from typing import Optional

# drama.* agent_id → Tier3 scope_key（按部门代码）
DRAMA_AGENT_SCOPE: dict[str, str] = {
    # 战略选题部
    "drama.topic-planner": "dept-strategy",
    "drama.world-architect": "dept-worldbuilding",
    "drama.character-designer": "dept-worldbuilding",
    "drama.plot-architect": "dept-plot",
    "drama.script-writer": "dept-writing",
    "drama.script-reviewer": "dept-review",
    "drama.quality-reporter": "dept-review",
    "drama.compliance-guard": "dept-ops",
}


def node_scope_for_agent(agent_id: str) -> str:
    """返回 Tier3 规则 scope_key；未知 Agent 返回空串（仅加载 global Tier）。"""
    key = (agent_id or "").strip()
    return DRAMA_AGENT_SCOPE.get(key, "")


def genre_from_project_payload(project_payload: dict) -> str:
    theme = (project_payload or {}).get("theme") or ""
    return str(theme).strip()
