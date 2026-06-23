# -*- coding: utf-8 -*-
"""Drama 执行产物展示服务。"""
from __future__ import annotations

from typing import Any, Dict

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.artifact_service import get_artifact
from apps.creation.models import Project
from apps.drama.models import DramaRoleExecution
from apps.drama.presentation.presenters import present_artifact
from apps.drama.services import DramaRoleRunService


def build_role_output_views(
    creation_project: Project,
    output_artifacts: Dict[str, Any],
    *,
    agent_id: str = "",
) -> Dict[str, dict]:
    """按角色 output_contract 构建展示视图。"""
    schema_by_key: Dict[str, str] = {}
    if agent_id:
        agent = AgentDefinitionService.get_runnable(agent_id)
        contract = agent.output_contract or {}
        schema_version = str(contract.get("schema_version") or "")
        for key in contract.get("artifacts") or []:
            schema_by_key[str(key)] = schema_version

    views: Dict[str, dict] = {}
    for key, payload in (output_artifacts or {}).items():
        if payload in (None, {}, []):
            payload = get_artifact(creation_project, key)
        if payload in (None, {}, []):
            continue
        schema = schema_by_key.get(key) or _infer_schema_version(key, payload)
        views[key] = present_artifact(key, schema, payload)
    return views


def build_execution_output_views(drama_exec: DramaRoleExecution) -> Dict[str, dict]:
    if drama_exec.status != DramaRoleExecution.Status.SUCCESS:
        return {}
    creation = DramaRoleRunService.ensure_creation_project(drama_exec.drama_project)
    return build_role_output_views(
        creation,
        drama_exec.output_artifacts or {},
        agent_id=drama_exec.agent_id,
    )


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
    }
    return fallback.get(artifact_key, "generic.v1")
