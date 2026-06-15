# -*- coding: utf-8 -*-
"""ScoreAgent：深度评分。"""
from __future__ import annotations

import logging

from ..artifact_service import get_artifact, save_artifact
from ..fusion.fusion_pipeline import run_fusion_score_for_project
from ..models import Project
from ..step_mode import build_pipeline_result_from_project
from .sub_skill_runner import (
    agent_execution_meta,
    mark_executed,
    persist_agent_execution_trace,
)
from .types import AgentResult

logger = logging.getLogger(__name__)


def run_score_agent(project: Project) -> AgentResult:
    pipeline_result = build_pipeline_result_from_project(project)
    try:
        fusion_out = run_fusion_score_for_project(project, pipeline_result)
    except Exception as exc:  # noqa: BLE001
        logger.exception("[ScoreAgent] failed project=%s", project.id)
        return AgentResult(agent_id="score", status="error", errors=[str(exc)])

    score_raw = get_artifact(project, "script_score_report") or {}
    report = {
        "agentId": "score",
        "overallScore": project.overall_score,
        "grade": project.grade,
        "fusionStatus": project.fusion_status,
        "scorePayload": score_raw,
        "ready": bool(fusion_out.get("ready")),
    }
    save_artifact(project, "score_report", report)

    # 触发爆款基线比对（非阻塞，失败不影响评分结果）
    try:
        from ..script_comparator import run_script_comparator

        brief = get_artifact(project, "project_brief") or {}
        genre = brief.get("genre") or ""
        run_script_comparator(project, genre=genre, top_n=3)
        mark_executed(executed, "script-comparator")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ScoreAgent] 爆款基线比对失败（已跳过）: %s", exc)

    executed = list(fusion_out.get("executed_sub_skills") or [])
    if not executed:
        mark_executed(executed, "score-deep")
    trace_meta = agent_execution_meta("score", executed, node_index=7)
    persist_agent_execution_trace(project, "score", executed)
    return AgentResult(
        agent_id="score",
        status="completed",
        outputs={"score_report": report},
        meta={**trace_meta, "fusion": fusion_out},
    )
