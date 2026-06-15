# -*- coding: utf-8 -*-
"""子技能对外 API 术语：skill_id / sub_skill_id（主链术语见 agent_term.py）。"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

JsonDict = Dict[str, Any]


def resolve_skill_id(data: Optional[Mapping[str, Any]]) -> str:
    """从请求体解析子技能 ID。"""
    if not data:
        return ""
    return str(data.get("skill_id") or data.get("sub_skill_id") or "").strip()


def alias_sub_skill_id(record: JsonDict) -> JsonDict:
    """子技能记录：规范 skill_id 字段。"""
    if not isinstance(record, dict):
        return record
    out = dict(record)
    sid = str(out.get("skill_id") or out.get("sub_skill_id") or out.get("id") or "").strip()
    if sid:
        out["skill_id"] = sid
    return out
