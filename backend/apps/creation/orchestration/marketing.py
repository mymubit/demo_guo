# -*- coding: utf-8 -*-
"""MarketingAgent：宣发物料。"""
from __future__ import annotations

from typing import Any, Dict

from ..artifact_service import get_artifact, save_artifact
from ..marketing_hooks import enrich_marketing_kit
from ..marketing_title_risk import review_title_risk
from ..models import Project
from .sub_skill_runner import (
    agent_execution_meta,
    mark_executed,
    persist_agent_execution_trace,
)
from .types import AgentResult


def _fallback_marketing_kit(project: Project, brief: dict, score: dict) -> Dict[str, Any]:
    title = brief.get("workingTitle") or project.title
    grade = score.get("grade") or project.grade or ""
    return {
        "titles": [title, f"{title}·高能反转"],
        "clipHooks": ["第1集前3秒：身份反转悬念", "中段打脸名场面"],
        "posterSlogans": [f"{title} — 每集都有钩子"],
        "grade": grade,
        "source": "fallback",
    }


def run_marketing_agent(project: Project) -> AgentResult:
    brief = get_artifact(project, "project_brief") or {}
    outline = get_artifact(project, "series_outline") or {}
    structure = get_artifact(project, "structure_plan") or {}
    score = get_artifact(project, "script_score_report") or get_artifact(project, "score_report") or {}

    title = (brief.get("workingTitle") or project.title or "未命名").strip()
    logline = (brief.get("coreHook") or project.core_idea or "")[:200]
    theme = (project.theme or brief.get("theme") or "mixed-theme").strip()
    episodes = int(outline.get("totalEpisodes") or project.episode_count or 60)

    executed: list = []
    kit: Dict[str, Any] = _fallback_marketing_kit(project, brief, score)
    mark_executed(executed, "marketing-kit")

    kit = enrich_marketing_kit(kit, brief=brief, outline=outline, structure_plan=structure)
    mark_executed(executed, "clip-hook-generator")

    title_risk = review_title_risk(title)
    kit["titleRiskReview"] = title_risk
    if title_risk.get("passed"):
        mark_executed(executed, "title-risk-review")
    else:
        mark_executed(executed, "title-risk-review")
        kit.setdefault("issues", []).extend(title_risk.get("issues") or [])

    kit["agentId"] = "marketing"
    save_artifact(project, "marketing_kit", kit)
    trace_meta = agent_execution_meta("marketing", executed, node_index=0)
    persist_agent_execution_trace(project, "marketing", executed)
    return AgentResult(
        agent_id="marketing",
        status="completed",
        outputs={"marketing_kit": kit},
        meta=trace_meta,
    )
