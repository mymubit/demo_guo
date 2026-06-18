# -*- coding: utf-8 -*-
"""从项目产物构建 script_delivery 所需的 pipeline_result 结构。"""
from __future__ import annotations

from typing import Any, Dict

from apps.workflow.fusion import get_artifact_registry

from .artifact_renderer import episode_scripts_to_legacy_scripts
from .artifact_service import get_artifact
from .models import Project


def build_pipeline_result_from_project(project: Project) -> Dict[str, Any]:
    registry = get_artifact_registry()
    artifacts: Dict[str, Any] = {}
    result: Dict[str, Any] = {
        "status": "completed",
        "review": {},
        "artifacts": artifacts,
    }
    for source in registry.pipeline_result_sources():
        artifact_key = source["artifact_key"]
        pipeline_key = source["pipeline_result_key"]
        payload = get_artifact(project, artifact_key) or {}
        artifacts[artifact_key] = payload
        if registry.uses_legacy_script_transform(pipeline_key):
            result[pipeline_key] = (
                episode_scripts_to_legacy_scripts(payload) if payload else {}
            )
        else:
            result[pipeline_key] = payload
    for legacy_key in ("project_brief", "structure", "characters", "outlines", "scripts"):
        result.setdefault(legacy_key, {})
    return result
