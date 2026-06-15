# -*- coding: utf-8 -*-
"""融合技能 Schema 注册表 — Phase C 优先 DB artifact 映射。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .config_loader import FusionSkillConfig, get_fusion_config

# 磁盘 fallback / Gate 产物（无独立 schema 文件）
MAIN_CHAIN_ARTIFACTS = {
    "project_brief": {
        "output_key": "projectBrief",
        "pipeline_result_key": "project_brief",
        "schema": "project-brief.schema.json",
        "node_id": "node-1-input",
    },
    "structure_plan": {
        "output_key": "structurePlan",
        "pipeline_result_key": "structure",
        "schema": "structure-plan.schema.json",
        "node_id": "node-2-structure",
    },
    "character_bible": {
        "output_key": "characterBible",
        "pipeline_result_key": "characters",
        "schema": "character-bible.schema.json",
        "node_id": "node-3-character",
    },
    "series_outline": {
        "output_key": "seriesOutline",
        "pipeline_result_key": "outlines",
        "schema": "series-outline.schema.json",
        "node_id": "node-4-outline",
    },
    "episode_scripts": {
        "output_key": "episodeScripts",
        "pipeline_result_key": "scripts",
        "schema": "episode-scripts.schema.json",
        "node_id": "node-5-script",
    },
    "quality_report": {
        "output_key": "qualityReport",
        "pipeline_result_key": "",
        "schema": "quality-report.schema.json",
        "node_id": "node-6-review",
    },
    "script_score_report": {
        "output_key": "scriptScoreReport",
        "pipeline_result_key": "",
        "schema": "script-score-report.schema.json",
        "node_id": "node-8-score",
    },
}

GATE_ARTIFACTS = {
    "gate_full": {"node_id": "node-6-review", "schema": None},
    "compliance": {"node_id": "node-6-review", "schema": None},
}


def _effective_main_chain_artifacts() -> Dict[str, Dict[str, Any]]:
    from apps.workflow.pipeline_store import FusionPipelineDbService

    return FusionPipelineDbService.main_chain_artifacts_map()


class FusionSchemaRegistry:
    def __init__(self, config: Optional[FusionSkillConfig] = None):
        self.config = config or get_fusion_config()

    def main_chain_artifact_keys(self) -> List[str]:
        return list(_effective_main_chain_artifacts().keys())

    def artifact_meta(self, artifact_key: str) -> Optional[Dict[str, Any]]:
        meta = _effective_main_chain_artifacts().get(artifact_key) or GATE_ARTIFACTS.get(artifact_key)
        if not meta:
            return None
        schema_file = meta.get("schema")
        from apps.workflow.pipeline_store import FusionPipelineDbService

        version = FusionPipelineDbService.active_version() or self.config.version
        return {
            **meta,
            "artifact_key": artifact_key,
            "schema_path": schema_file,
            "skill_version": version,
        }

    def schema_file_for_artifact(self, artifact_key: str) -> Optional[str]:
        meta = _effective_main_chain_artifacts().get(artifact_key)
        if not meta:
            return None
        return meta.get("schema")

    def nodes_for_api(self) -> List[Dict[str, Any]]:
        from .registry import FusionNodeRegistry

        return FusionNodeRegistry(self.config).main_chain_nodes()
