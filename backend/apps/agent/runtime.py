# -*- coding: utf-8 -*-
"""Agent 中心 — 运行时 registry 缓存读。"""
from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from django.utils.module_loading import import_string

from apps.common.agent_term import AGENT_RUNNER_PREFIX, normalize_agent_runner_path

logger = logging.getLogger(__name__)

_RUNNER_IMPORT_PREFIX = AGENT_RUNNER_PREFIX
_EMPTY_REGISTRY: Dict[str, Any] = {"agents": [], "_meta": {}, "_registry_source": "none"}
_SCRIPT_FORGE_WORKSPACE_MAP: Dict[int, str] = {
    1: "brief",
    2: "structure",
    3: "character",
    4: "outline",
    5: "script",
}
_SCRIPT_FORGE_AGENT_DEFS: Dict[str, Dict[str, Any]] = {
    "brief": {"id": "brief", "name": "Brief Agent", "workspace_index": 1, "outputs": ["project_brief"]},
    "structure": {"id": "structure", "name": "Structure Agent", "workspace_index": 2, "outputs": ["structure_plan"]},
    "character": {"id": "character", "name": "Character Agent", "workspace_index": 3, "outputs": ["character_bible"]},
    "outline": {"id": "outline", "name": "Outline Agent", "workspace_index": 4, "outputs": ["series_outline"]},
    "script": {"id": "script", "name": "Script Agent", "workspace_index": 5, "outputs": ["episode_scripts"]},
    "review": {"id": "review", "name": "Review Agent", "outputs": ["review_report"]},
    "score": {"id": "score", "name": "Score Agent", "outputs": ["script_score_report"]},
    "polish": {"id": "polish", "name": "Polish Agent", "outputs": ["episode_scripts", "polish_log"]},
    "marketing": {"id": "marketing", "name": "Marketing Agent", "outputs": ["marketing_kit"]},
    "insight": {"id": "insight", "name": "Insight Agent", "outputs": ["insight_report"]},
}


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


_REGISTRY_CACHE: Dict[str, Any] = {}
_REGISTRY_CACHE_TTL = 60  # 秒，配置改动 60s 内生效，无需重启 worker
_REGISTRY_CACHE_AT: float = 0.0


def get_agent_registry() -> Dict[str, Any]:
    global _REGISTRY_CACHE, _REGISTRY_CACHE_AT
    now = time.monotonic()
    if _REGISTRY_CACHE and (now - _REGISTRY_CACHE_AT) < _REGISTRY_CACHE_TTL:
        return _REGISTRY_CACHE
    data = _get_agent_registry_impl()
    _REGISTRY_CACHE = data
    _REGISTRY_CACHE_AT = now
    return data


def clear_agent_registry_cache() -> None:
    global _REGISTRY_CACHE, _REGISTRY_CACHE_AT
    _REGISTRY_CACHE = {}
    _REGISTRY_CACHE_AT = 0.0


get_agent_registry.cache_clear = clear_agent_registry_cache  # type: ignore[attr-defined]


def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    reg = get_agent_registry()
    for agent in reg.get("agents") or []:
        if agent.get("id") == agent_id:
            return agent
    builtin = _SCRIPT_FORGE_AGENT_DEFS.get(str(agent_id or "").strip())
    return dict(builtin) if builtin else None


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
        return normalize_agent_runner_path(configured)
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
    if all(mapping.get(idx) == aid for idx, aid in _SCRIPT_FORGE_WORKSPACE_MAP.items()):
        return mapping
    mapping = _agents_workspace_index_mapping()
    if all(mapping.get(idx) == aid for idx, aid in _SCRIPT_FORGE_WORKSPACE_MAP.items()):
        return mapping
    return dict(_SCRIPT_FORGE_WORKSPACE_MAP)


def workspace_index_for_agent(agent_id: str) -> Optional[int]:
    for idx, aid in workspace_agent_map().items():
        if aid == agent_id:
            return idx
    return None


def agent_for_workspace_index(node_index: int) -> Optional[str]:
    return workspace_agent_map().get(int(node_index))


def agent_for_pipeline_node_index(node_index: int) -> Optional[str]:
    idx = int(node_index)
    return workspace_agent_map().get(idx)


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
