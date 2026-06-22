# -*- coding: utf-8 -*-
"""
artifact_key 工具 — drama.* 新体系。

旧的 get_artifact_registry() 依赖已移除。
直接使用 drama.* 产物键集合。
"""
from __future__ import annotations

from typing import List

# drama.* 核心产物键集合
DRAMA_ARTIFACT_KEYS: List[str] = [
    "project_brief",
    "world_setting",
    "character_bible",
    "series_outline",
    "episode_scripts",
    "emotion_blueprint",
    "emotion_curve",
    "hook_plan",
    "conflict_plan",
    "reversal_plan",
    "review_report",
    "reader_review",
    "emotion_audit",
    "quality_report",
    "compliance_report",
    "word_count_report",
    "style_check",
    "visual_pack",
    "storyboard",
    "post_assets",
    "marketing_kit",
    "delivery_pack",
    "evolution_proposal",
    "adaptation_plan",
    "lapian_report",
    "market_analysis",
    "formula_analysis",
    "dream_check",
    "psychology_guide",
    "visual_prompts",
]

# 可能包含逐集数据（数组型产物）
ARRAY_ARTIFACT_KEYS = frozenset({
    "episode_scripts",
    "series_outline",
    "emotion_curve",
    "emotion_blueprint",
    "storyboard",
})


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
