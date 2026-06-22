# -*- coding: utf-8 -*-
"""从项目产物构建交付所需的结果结构 — drama.* 新体系。

旧的 get_artifact_registry() / pipeline_result_sources() 依赖已移除。
现在直接使用 drama.* 产物键映射。
"""
from __future__ import annotations

from typing import Any, Dict

from .artifact_renderer import normalize_episode_scripts_for_delivery
from .artifact_service import get_artifact
from .models import Project

# drama.* 产物键 → 结果字段名映射
DRAMA_ARTIFACT_RESULT_KEYS: Dict[str, str] = {
    "project_brief": "project_brief",
    "world_setting": "world_setting",
    "character_bible": "character_bible",
    "series_outline": "series_outline",
    "episode_scripts": "scripts",  # 保留 scripts 兼容旧交付格式
    "quality_report": "quality_report",
    "compliance_report": "compliance_report",
    "delivery_pack": "delivery_pack",
    "emotion_curve": "emotion_curve",
    "emotion_blueprint": "emotion_blueprint",
    "marketing_kit": "marketing_kit",
}

# 需要 episode_scripts → scripts 格式转换的键
_SCRIPT_TRANSFORM_KEYS = frozenset({"scripts"})


def build_pipeline_result_from_project(project: Project) -> Dict[str, Any]:
    """构建项目的完整产物结果结构（用于交付/预览）。"""
    artifacts: Dict[str, Any] = {}
    result: Dict[str, Any] = {
        "status": "completed",
        "artifacts": artifacts,
    }

    for artifact_key, result_key in DRAMA_ARTIFACT_RESULT_KEYS.items():
        payload = get_artifact(project, artifact_key) or {}
        artifacts[artifact_key] = payload

        if result_key in _SCRIPT_TRANSFORM_KEYS and payload:
            result[result_key] = normalize_episode_scripts_for_delivery(payload)
        else:
            result[result_key] = payload

    return result
