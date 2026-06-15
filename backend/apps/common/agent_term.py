# -*- coding: utf-8 -*-
"""主链 Agent 对外 API 术语：响应只输出 agent_id；请求体仍接受 skill_id 废弃别名。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

JsonDict = Dict[str, Any]

DEPRECATED_API_FIELDS: Dict[str, str] = {
    "skill_id": "agent_id",
    "skillId": "agentId",
    "default_tier1_sections_by_skill": "default_tier1_sections_by_agent",
}


def api_deprecation_meta() -> Dict[str, str]:
    return dict(DEPRECATED_API_FIELDS)


def attach_api_meta(payload: JsonDict) -> JsonDict:
    if not isinstance(payload, dict):
        return payload
    out = dict(payload)
    meta = dict(out.get("api_meta") or {})
    meta["deprecated_fields"] = api_deprecation_meta()
    out["api_meta"] = meta
    return out


def attach_deprecated_paths(payload: JsonDict, paths: List[str]) -> JsonDict:
    if not isinstance(payload, dict):
        return payload
    out = dict(payload)
    meta = dict(out.get("api_meta") or {})
    existing = list(meta.get("deprecated_paths") or [])
    meta["deprecated_paths"] = existing + [p for p in paths if p not in existing]
    out["api_meta"] = meta
    return out


def resolve_agent_id(data: Optional[Mapping[str, Any]]) -> str:
    if not data:
        return ""
    return str(data.get("agent_id") or data.get("skill_id") or "").strip()


def alias_agent_id(record: JsonDict) -> JsonDict:
    """对外 API 记录：只输出 agent_id / agentId，移除 skill_id 主链别名。"""
    if not isinstance(record, dict):
        return record
    out = dict(record)
    aid = (
        str(out.get("agent_id") or out.get("skill_id") or out.get("agentId") or out.get("skillId") or "")
        .strip()
    )
    if aid:
        out["agent_id"] = aid
        out["agentId"] = aid
    out.pop("skill_id", None)
    out.pop("skillId", None)
    return out


def alias_agent_id_list(items: List[Any]) -> List[Any]:
    return [alias_agent_id(x) if isinstance(x, dict) else x for x in items]


def enrich_registry_for_api(registry: JsonDict) -> JsonDict:
    """GET 响应：registry._meta 模块列表与 agents 列表使用 agent_id。"""
    if not isinstance(registry, dict):
        return registry
    out = dict(registry)
    meta = out.get("_meta")
    if isinstance(meta, dict):
        meta_out = dict(meta)
        for key in ("workspace_modules", "post_script_pipeline_index"):
            if key in meta_out and isinstance(meta_out[key], list):
                meta_out[key] = alias_agent_id_list(meta_out[key])
        out["_meta"] = meta_out
    agents = out.get("agents")
    if isinstance(agents, list):
        out["agents"] = [
            alias_agent_id({**a, "agent_id": a.get("id")}) if isinstance(a, dict) and a.get("id") else a
            for a in agents
        ]
    return out


def normalize_registry_for_save(registry: JsonDict) -> JsonDict:
    """PUT 请求：skill_id 别名写入 agent_id 后落库。"""
    if not isinstance(registry, dict):
        return registry
    out = dict(registry)
    meta = out.get("_meta")
    if not isinstance(meta, dict):
        return out

    def _normalize_modules(modules: Any) -> Any:
        if not isinstance(modules, list):
            return modules
        normalized: List[JsonDict] = []
        for item in modules:
            if not isinstance(item, dict):
                normalized.append(item)
                continue
            row = dict(item)
            aid = resolve_agent_id(row)
            if aid:
                row["agent_id"] = aid
            row.pop("skill_id", None)
            normalized.append(row)
        return normalized

    meta_out = dict(meta)
    for key in ("workspace_modules", "post_script_pipeline_index"):
        if key in meta_out:
            meta_out[key] = _normalize_modules(meta_out[key])
    out["_meta"] = meta_out
    return out
