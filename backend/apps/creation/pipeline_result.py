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

# 需要 episode_scripts → scripts 格式转换的键
_SCRIPT_TRANSFORM_KEYS = frozenset({"scripts"})


def _pipeline_result_key_map() -> Dict[str, str]:
    from apps.drama.skills_registry import get_pipeline_result_key_map

    return get_pipeline_result_key_map()


def build_pipeline_result_from_project(project: Project) -> Dict[str, Any]:
    """构建项目的完整产物结果结构（用于交付/预览）。"""
    artifacts: Dict[str, Any] = {}
    result: Dict[str, Any] = {
        "status": "completed",
        "artifacts": artifacts,
    }

    for artifact_key, result_key in _pipeline_result_key_map().items():
        payload = get_artifact(project, artifact_key) or {}
        artifacts[artifact_key] = payload

        if result_key in _SCRIPT_TRANSFORM_KEYS and payload:
            result[result_key] = normalize_episode_scripts_for_delivery(payload)
        else:
            result[result_key] = payload

    return result
