# -*- coding: utf-8 -*-
"""Drama Skills 12 角色默认定义 — 数据来自 drama-skills/registry.yaml（Git SSOT）。"""
from __future__ import annotations

from typing import Any, Dict, List

from apps.drama.skills_registry import (
    build_role_defaults,
    get_departments,
    get_fast_track_agent_ids,
    get_visible_agent_ids,
)

DRAMA_DEPARTMENTS: List[Dict[str, Any]] = get_departments()
DRAMA_FAST_TRACK_ROLES: List[str] = get_fast_track_agent_ids()
DRAMA_VISIBLE_ROLES: List[str] = get_visible_agent_ids()
DRAMA_ROLE_DEFAULTS: List[Dict[str, Any]] = build_role_defaults()


def get_role_by_id(agent_id: str) -> Dict[str, Any]:
    for role in DRAMA_ROLE_DEFAULTS:
        if role["agent_id"] == agent_id:
            return role
    return {}


def get_visible_roles() -> List[Dict[str, Any]]:
    return DRAMA_ROLE_DEFAULTS


def get_roles_by_dept(dept_code: str) -> List[Dict[str, Any]]:
    return [r for r in DRAMA_ROLE_DEFAULTS if r["dept"] == dept_code]


def get_fast_track_roles() -> List[Dict[str, Any]]:
    return [r for r in DRAMA_ROLE_DEFAULTS if r["agent_id"] in DRAMA_FAST_TRACK_ROLES]
