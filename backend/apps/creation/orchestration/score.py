# -*- coding: utf-8 -*-
"""Explicit ScoreAgent without external Fusion runtime."""
from __future__ import annotations

import logging

from ..artifact_service import get_artifact, save_artifact
from ..models import Project
from .sub_skill_runner import agent_execution_meta, mark_executed, persist_agent_execution_trace
from .types import AgentResult

logger = logging.getLogger(__name__)


def _grade_for_score(score):
    if score is None:
        return ""
    try:
        value = float(score)
    except (TypeError, ValueError):
        return ""
    if value >= 90:
        return "S"
    if value >= 80:
        return "A"
    if value >= 70:
        return "B"
    if value >= 60:
        return "C"
    return "D"


def run_score_agent(project: Project) -> AgentResult:
    existing = get_artifact(project, "script_score_report") or get_artifact(project, "score_report") or {}
    scripts = get_artifact(project, "episode_scripts") or {}
    episodes = scripts.get("episodes") or []
    overall = existing.get("overallScore")
    if overall is None:
        overall = project.overall_score
    grade = existing.get("grade") or project.grade or _grade_for_score(overall)
    report = {
        "agentId": "score",
        "overallScore": overall,
        "grade": grade or "",
        "ready": bool(episodes),
        "source": "python-native",
        "scorePayload": existing,
    }
    save_artifact(project, "score_report", report)
    save_artifact(project, "script_score_report", report)

    update_fields = []
    if overall is not None:
        project.overall_score = overall
        update_fields.append("overall_score")
    if grade:
        project.grade = str(grade)[:16]
        update_fields.append("grade")
    if update_fields:
        update_fields.append("updated_at")
        project.save(update_fields=update_fields)

    executed = []
    mark_executed(executed, "score-deep")
    trace_meta = agent_execution_meta("score", executed, node_index=0)
    persist_agent_execution_trace(project, "score", executed)
    return AgentResult(
        agent_id="score",
        status="completed",
        outputs={"score_report": report},
        meta=trace_meta,
    )
