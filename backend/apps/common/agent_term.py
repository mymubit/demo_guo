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

LEGACY_AGENT_RUNNER_PREFIX = "apps.creation.agents."
AGENT_RUNNER_PREFIX = "apps.creation.orchestration."

PIPELINE_RUNNER_BY_TYPE: Dict[str, str] = {
    "fusion_node": "apps.creation.step_mode.run_orchestrator_step",
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


def normalize_agent_runner_path(path: Any) -> str:
    """规范化 Agent runner 路径。
    - 旧路径 apps.creation.agents.* → 清空（已下线）
    - apps.creation.orchestration.* → 保留（工作台 Agent 编排入口）
    """
    text = str(path or "").strip()
    if text.startswith(LEGACY_AGENT_RUNNER_PREFIX):
        return ""
    return text


def normalize_pipeline_runner_path(path: Any, runner_type: Any = "") -> str:
    """规范化 FusionPipelineNode.runner_path，避免把 Agent runner 挂到步骤 runner 上。"""
    text = str(path or "").strip()
    rtype = str(runner_type or "").strip()
    if text.startswith(LEGACY_AGENT_RUNNER_PREFIX):
        return PIPELINE_RUNNER_BY_TYPE.get(rtype, "")
    if text.startswith(AGENT_RUNNER_PREFIX):
        return PIPELINE_RUNNER_BY_TYPE.get(rtype, "")
    return text or PIPELINE_RUNNER_BY_TYPE.get(rtype, "")


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
        for key in ("workspace_modules",):
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
    """PUT 请求：skill_id 别名写入 agent_id，并规范化历史 runner 路径后落库。"""
    if not isinstance(registry, dict):
        return registry
    out = dict(registry)
    meta = out.get("_meta")

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

    if isinstance(meta, dict):
        meta_out = dict(meta)
        for key in ("workspace_modules",):
            if key in meta_out:
                meta_out[key] = _normalize_modules(meta_out[key])
        meta_out.pop("post_script_pipeline_index", None)
        meta_out.pop("post_script_chain", None)
        meta_out.pop("post_script_append_agents", None)
        out["_meta"] = meta_out

    agents = out.get("agents")
    if isinstance(agents, list):
        normalized_agents: List[JsonDict] = []
        for agent in agents:
            if not isinstance(agent, dict):
                normalized_agents.append(agent)
                continue
            row = dict(agent)
            for key in ("runner", "runner_path"):
                if key in row:
                    row[key] = normalize_agent_runner_path(row[key])
            normalized_agents.append(row)
        out["agents"] = normalized_agents
    return out
