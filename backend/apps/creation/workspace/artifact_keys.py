# -*- coding: utf-8 -*-
"""
artifact_key 工具 — drama.* 新体系。

旧的 get_artifact_registry() 依赖已移除。
直接使用 drama.* 产物键集合。
"""
from __future__ import annotations

from typing import List

from apps.drama.skills_registry import build_role_defaults, get_array_artifact_keys


def _collect_registry_artifact_keys() -> List[str]:
    keys: set[str] = {"project_brief"}
    for role in build_role_defaults():
        if role.get("default_output_artifact_key"):
            keys.add(str(role["default_output_artifact_key"]))
        for contract_name in ("input_contract", "output_contract"):
            contract = role.get(contract_name) or {}
            for key in contract.get("required_artifacts") or []:
                keys.add(str(key))
            for key in contract.get("artifacts") or []:
                keys.add(str(key))
    return sorted(keys)


# drama.* 核心产物键集合（registry 主产物 + 契约引用）
DRAMA_ARTIFACT_KEYS: List[str] = _collect_registry_artifact_keys()

ARRAY_ARTIFACT_KEYS = get_array_artifact_keys()


def is_array_artifact(artifact_key: str) -> bool:
    """判断是否是数组型产物（含逐集数据）。"""
    return artifact_key in ARRAY_ARTIFACT_KEYS


def primary_artifact_for_agent(agent_id: str) -> str:
    """获取 drama.* Agent 的主要产物键。"""
    from apps.creation.agent_runtime.chunk_service import get_agent_primary_artifact
    return get_agent_primary_artifact(agent_id) or ""


def artifact_key_for_node(node_index: int) -> str:
    """工作台节点索引 → 产物键（兼容独立工作台 1–5 段式编辑）。"""
    return {
        1: "project_brief",
        2: "structure_plan",
        3: "character_bible",
        4: "series_outline",
        5: "episode_scripts",
    }.get(int(node_index), "")


def node_index_for_artifact(artifact_key: str) -> int:
    """产物键 → 工作台节点索引。"""
    mapping = {
        "project_brief": 1,
        "structure_plan": 2,
        "character_bible": 3,
        "series_outline": 4,
        "episode_scripts": 5,
    }
    return mapping.get(str(artifact_key or "").strip(), 0)
