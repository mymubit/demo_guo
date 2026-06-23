# -*- coding: utf-8 -*-
"""Drama 执行产物展示服务。"""
from __future__ import annotations

import logging
from typing import Any, Dict

from apps.agent.definition_service import AgentDefinitionService
from apps.drama.models import DramaRoleExecution
from apps.drama.presentation.base import view
from apps.drama.presentation.presenters import present_artifact

logger = logging.getLogger(__name__)


def build_role_output_views(
    output_artifacts: Dict[str, Any],
    *,
    agent_id: str = "",
) -> Dict[str, dict]:
    """仅依据 execution 快照中的 output_artifacts 构建展示视图。"""
    schema_by_key: Dict[str, str] = {}
    artifact_keys: list[str] = []
    if agent_id:
        agent = AgentDefinitionService.get_runnable(agent_id)
        contract = agent.output_contract or {}
        schema_version = str(contract.get("schema_version") or "")
        for key in contract.get("artifacts") or []:
            key_str = str(key)
            schema_by_key[key_str] = schema_version
            artifact_keys.append(key_str)

    if output_artifacts:
        for key in output_artifacts:
            key_str = str(key)
            if key_str not in artifact_keys:
                artifact_keys.append(key_str)

    views: Dict[str, dict] = {}
    for key in artifact_keys:
        payload = (output_artifacts or {}).get(key)
        if payload in (None, {}, []):
            continue
        schema = schema_by_key.get(key) or _infer_schema_version(key, payload)
        try:
            views[key] = present_artifact(key, schema, payload)
        except Exception:  # noqa: BLE001
            logger.exception("[DramaPresentation] 产物展示失败 artifact=%s schema=%s", key, schema)
            views[key] = view(
                key,
                schema,
                [],
                summary="展示暂不可用，请查看原始 JSON",
            )
    return views


def build_execution_output_views(drama_exec: DramaRoleExecution) -> Dict[str, dict]:
    if drama_exec.status != DramaRoleExecution.Status.SUCCESS:
        return {}
    artifacts = dict(drama_exec.output_artifacts or {})
    return build_role_output_views(artifacts, agent_id=drama_exec.agent_id)


def _infer_schema_version(artifact_key: str, payload: Any) -> str:
    if isinstance(payload, dict):
        meta = payload.get("_meta") or {}
        schema = meta.get("schemaVersion") or meta.get("schema_version")
        if schema:
            return str(schema)
    fallback = {
        "project_brief": "project-brief.v1",
        "character_bible": "character-bible.v1",
        "series_outline": "series-outline.v1",
        "episode_scripts": "episode-scripts.v1",
        "review_report": "review-report.v1",
        "quality_report": "quality-report.v1",
        "compliance_report": "compliance-report.v1",
        "marketing_kit": "marketing-kit.v1",
        "market_report": "market-report.v1",
        "narrative_plan": "narrative-plan.v1",
    }
    return fallback.get(artifact_key, "generic.v1")
