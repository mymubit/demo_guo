# -*- coding: utf-8 -*-
"""Drama 执行产物展示服务。"""
from __future__ import annotations

import logging
from typing import Any, Dict

from apps.agent.definition_service import AgentDefinitionService
from apps.drama.models import DramaRoleExecution
from apps.drama.presentation.base import view
from apps.drama.presentation.presenters import present_artifact

from apps.drama.presentation.artifact_source import resolve_live_output_artifacts

logger = logging.getLogger(__name__)


def build_role_output_views(
    output_artifacts: Dict[str, Any],
    *,
    agent_id: str = "",
    planned_episodes: int | None = None,
    outline_progress: Dict[str, Any] | None = None,
) -> Dict[str, dict]:
    """依据 execution 快照中的 output_artifacts 构建展示视图。"""
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
            if key == "series_outline":
                from apps.drama.presentation.schema_presenters import present_series_outline

                views[key] = present_series_outline(
                    key,
                    payload,
                    planned_episodes=planned_episodes,
                    outline_progress=outline_progress,
                )
            else:
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


def build_execution_output_views(
    drama_exec: DramaRoleExecution,
    *,
    planned_episodes: int | None = None,
    outline_progress: Dict[str, Any] | None = None,
) -> Dict[str, dict]:
    if drama_exec.status != DramaRoleExecution.Status.SUCCESS:
        return {}
    artifacts = resolve_live_output_artifacts(drama_exec)
    if planned_episodes is None and getattr(drama_exec, "project", None):
        planned_episodes = int(drama_exec.project.episode_count or 0) or None
    if outline_progress is None and drama_exec.agent_id == "drama.series-architect" and getattr(
        drama_exec, "project", None
    ):
        from apps.drama.outline_progress import summarize_series_outline_progress

        outline_progress = summarize_series_outline_progress(drama_exec.project)
    return build_role_output_views(
        artifacts,
        agent_id=drama_exec.agent_id,
        planned_episodes=planned_episodes,
        outline_progress=outline_progress,
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
        "market_report": "market-report.v1",
        "narrative_plan": "narrative-plan.v1",
    }
    return fallback.get(artifact_key, "generic.v1")
