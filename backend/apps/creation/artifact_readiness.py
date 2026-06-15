# -*- coding: utf-8 -*-
"""上游产物就绪判定与用户可读缺依赖提示。"""
from __future__ import annotations

from typing import Optional, Tuple

from .artifact_service import get_artifact
from .display.character_display import build_character_bible_view
from .models import Project
from .outline_skeleton import stage_rough_outline_ready
from .step_mode import artifact_key_for_node

UPSTREAM_ARTIFACT_LABELS = {
    "project_brief": "立项策划",
    "structure_plan": "结构与世界观",
    "character_bible": "角色设计",
    "series_outline": "大纲与创作规划",
    "episode_scripts": "剧集剧本",
}

ARTIFACT_NODE_INDEX = {
    "project_brief": 1,
    "structure_plan": 2,
    "character_bible": 3,
    "series_outline": 4,
    "episode_scripts": 5,
}


def missing_upstream_error(artifact_key: str) -> str:
    label = UPSTREAM_ARTIFACT_LABELS.get(artifact_key, artifact_key)
    return f"请先生成「{label}」"


def node_has_meaningful_content(project: Project, node_index: int) -> bool:
    key = artifact_key_for_node(node_index)
    if not key:
        return False
    payload = get_artifact(project, key)
    if not isinstance(payload, dict) or not payload:
        return False

    if node_index == 3:
        return int(build_character_bible_view(payload).get("characterCount") or 0) > 0

    if node_index == 4:
        if stage_rough_outline_ready(payload):
            return True
        for ep in payload.get("episodes") or []:
            if not isinstance(ep, dict):
                continue
            if (ep.get("oneLineSummary") or ep.get("summary") or "").strip():
                return True
        return False

    return True


def require_upstream_artifacts(
    project: Project,
    keys: Tuple[str, ...],
) -> Optional[str]:
    for key in keys:
        node_index = ARTIFACT_NODE_INDEX.get(key)
        if node_index is not None:
            if not node_has_meaningful_content(project, node_index):
                return missing_upstream_error(key)
            continue
        if not get_artifact(project, key):
            return missing_upstream_error(key)
    return None
