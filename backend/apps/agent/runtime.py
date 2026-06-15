# -*- coding: utf-8 -*-
"""Agent 中心 — 运行时 registry 缓存读。"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional

from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)

_RUNNER_IMPORT_PREFIX = "apps.creation.orchestration."
_EMPTY_REGISTRY: Dict[str, Any] = {"agents": [], "_meta": {}, "_registry_source": "none"}


def _parse_meta_index_list(items: Any) -> Dict[int, str]:
    mapping: Dict[int, str] = {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        try:
            idx = int(item.get("index"))
        except (TypeError, ValueError):
            continue
        agent_id = str(item.get("agent_id") or "").strip()
        if idx > 0 and agent_id:
            mapping[idx] = agent_id
    return mapping


def _agents_workspace_index_mapping() -> Dict[int, str]:
    mapping: Dict[int, str] = {}
    for agent in get_agent_registry().get("agents") or []:
        if not isinstance(agent, dict):
            continue
        idx = agent.get("workspace_index")
        agent_id = str(agent.get("id") or "").strip()
        if idx and agent_id:
            try:
                mapping[int(idx)] = agent_id
            except (TypeError, ValueError):
                continue
    return mapping


def _read_registry_from_db() -> Optional[Dict[str, Any]]:
    try:
        from django.db.utils import OperationalError, ProgrammingError

        from apps.agent.models import AgentRegistryConfig

        row = AgentRegistryConfig.objects.filter(is_active=True).order_by("-updated_at").first()
        if row and isinstance(row.registry, dict) and row.registry.get("agents"):
            data = dict(row.registry)
            data["_registry_source"] = "db"
            data["_registry_config_id"] = str(row.id)
            return data
    except (OperationalError, ProgrammingError):
        return None
    except Exception as exc:  # noqa: BLE001
        if type(exc).__name__ != "DatabaseOperationForbidden":
            logger.warning("[AgentRegistry] DB registry load failed: %s", exc)
    return None


def _get_agent_registry_impl() -> Dict[str, Any]:
    data = _read_registry_from_db()
    if data is not None:
        return data

    try:
        from apps.agent.registry import AgentRegistryConfigService

        AgentRegistryConfigService.ensure_defaults()
    except Exception as exc:  # noqa: BLE001
        logger.warning("[AgentRegistry] bootstrap failed: %s", exc)

    data = _read_registry_from_db()
    if data is not None:
        return data
    return dict(_EMPTY_REGISTRY)


@lru_cache(maxsize=1)
def get_agent_registry() -> Dict[str, Any]:
    return _get_agent_registry_impl()


def clear_agent_registry_cache() -> None:
    get_agent_registry.cache_clear()


def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    reg = get_agent_registry()
    for agent in reg.get("agents") or []:
        if agent.get("id") == agent_id:
            return agent
    return None


def primary_output_artifact(agent_id: str) -> str:
    agent = get_agent(agent_id) or {}
    for item in agent.get("outputs") or []:
        if isinstance(item, str) and item.strip():
            return item.strip()
    return ""


def agent_runner_path(agent_id: str) -> str:
    agent = get_agent(agent_id) or {}
    configured = str(agent.get("runner") or agent.get("runner_path") or "").strip()
    if configured:
        return configured
    normalized = str(agent_id or "").strip().replace("-", "_")
    return f"{_RUNNER_IMPORT_PREFIX}{normalized}.run_{normalized}_agent"


def resolve_agent_runner(agent_id: str) -> Optional[Callable[..., Any]]:
    path = agent_runner_path(agent_id)
    if not path.startswith(_RUNNER_IMPORT_PREFIX):
        logger.warning("[AgentRegistry] runner path rejected agent=%s path=%s", agent_id, path)
        return None
    try:
        return import_string(path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[AgentRegistry] runner import failed agent=%s path=%s err=%s", agent_id, path, exc)
        return None


def workspace_agent_map() -> Dict[int, str]:
    meta = get_agent_registry().get("_meta") or {}
    mapping = _parse_meta_index_list(meta.get("workspace_modules"))
    if mapping:
        return mapping
    return _agents_workspace_index_mapping()


def post_script_pipeline_index_map() -> Dict[int, str]:
    meta = get_agent_registry().get("_meta") or {}
    return _parse_meta_index_list(meta.get("post_script_pipeline_index"))


def workspace_index_for_agent(agent_id: str) -> Optional[int]:
    for idx, aid in workspace_agent_map().items():
        if aid == agent_id:
            return idx
    return None


def agent_for_workspace_index(node_index: int) -> Optional[str]:
    return workspace_agent_map().get(int(node_index))


def agent_for_pipeline_node_index(node_index: int) -> Optional[str]:
    idx = int(node_index)
    return workspace_agent_map().get(idx) or post_script_pipeline_index_map().get(idx)


def pipeline_action_display_name(action_key: str) -> str:
    key = (action_key or "").strip()
    if not key.startswith("pipeline.node."):
        return ""
    try:
        idx = int(key.rsplit(".", 1)[-1])
    except (TypeError, ValueError):
        return ""
    aid = agent_for_pipeline_node_index(idx)
    if not aid:
        return f"步骤 {idx}"
    agent = get_agent(aid) or {}
    name_zh = agent.get("name_zh") or aid
    name = agent.get("name") or aid
    return f"{idx}. {name_zh} ({name})"


def action_key_agent_meta(action_key: str) -> Dict[str, str]:
    key = (action_key or "").strip()
    if not key.startswith("pipeline.node."):
        return {}
    try:
        idx = int(key.rsplit(".", 1)[-1])
    except (TypeError, ValueError):
        return {}
    aid = agent_for_pipeline_node_index(idx)
    if not aid:
        return {}
    agent = get_agent(aid) or {}
    return {
        "agent_id": aid,
        "agent_name": agent.get("name") or aid,
        "agent_name_zh": agent.get("name_zh") or aid,
        "pipeline_step": str(idx),
    }


def post_script_chain() -> List[str]:
    reg = get_agent_registry()
    meta = reg.get("_meta") or {}
    return list(meta.get("post_script_chain") or reg.get("post_script_chain") or [])


def post_script_append_agents() -> List[str]:
    meta = get_agent_registry().get("_meta") or {}
    return list(meta.get("post_script_append_agents") or ["marketing"])


def post_script_effective_chain() -> List[str]:
    chain = list(post_script_chain() or [])
    for agent_id in post_script_append_agents():
        if agent_id and agent_id not in chain:
            chain.append(agent_id)
    return chain


def should_defer_to_post_script_chain(project, node_index: int) -> bool:
    """技能工作台：pipeline 尾部节点（质检/评分等）由 post_script_chain 统一执行。"""
    from apps.creation.models import Project

    if getattr(project, "pipeline_mode", None) != Project.MODE_WORKSPACE:
        return False
    return int(node_index) in post_script_pipeline_index_map()


def polish_max_rounds() -> int:
    meta = get_agent_registry().get("_meta") or {}
    return int(meta.get("polish_max_rounds") or 2)


def pacing_heuristics_rules() -> Dict[str, Any]:
    review = get_agent("review") or {}
    for skill in review.get("sub_skills") or []:
        if skill.get("id") == "pacing-keyword-heuristics":
            return skill.get("rules") or {}
    return {}


def list_agents() -> List[Dict[str, Any]]:
    return list(get_agent_registry().get("agents") or [])
