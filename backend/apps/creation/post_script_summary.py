# -*- coding: utf-8 -*-
"""剧本全量生成后的质检/润色/评分摘要（工作台 + 作品页共用）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .artifact_service import get_artifact
from .models import Project
from .node_preview import _safe_insight_summary, _safe_marketing_summary, _safe_polish_summary
from .display.portal_display import portal_sanitize_review_block, portal_strip_agent_block


def _build_post_script_chain_display() -> List[str]:
    """drama.* 创作完成后的后续处理角色链。"""
    return [
        "drama.script-scorer",
        "drama.revision-master",
        "drama.compliance-guard",
        "drama.delivery-tool",
    ]


def _latest_run_block(project: Project, agent_id: str) -> Optional[dict]:
    from .monitoring.execution_run_service import AgentExecutionRunService
    from .models import Project as ProjectModel

    if not isinstance(project, ProjectModel):
        return None
    return AgentExecutionRunService.latest_run_for_agent(project, agent_id=agent_id)


def _optional_node_status(run: Optional[dict], has_content: bool) -> str:
    """
    将 execution run + artifact 内容映射为前端可直接使用的状态字符串：
      not_run       — 从未执行过
      running       — 正在执行
      completed     — 已完成且有产物
      completed_empty — 已完成但产物为空（edge case）
      failed        — 执行失败
    """
    if run is None:
        return "not_run"
    status = run.get("status") or ""
    if status == "running":
        return "running"
    if status == "failed":
        return "failed"
    if status == "completed":
        return "completed" if has_content else "completed_empty"
    return "not_run"


def _scripts_fully_generated(project: Project) -> bool:
    """直接读 episode_scripts 产物判断剧本是否完整生成（不依赖旧引擎）。"""
    scripts = get_artifact(project, "episode_scripts") or {}
    eps = scripts.get("episodes") or []
    if not eps:
        return False
    nums = {
        int(e.get("episodeNumber") or e.get("episode") or 0)
        for e in eps
        if isinstance(e, dict)
    }
    nums.discard(0)
    target = int(project.episode_count or 0)
    if target <= 0:
        return len(nums) > 0
    return len(nums) >= target


def build_post_script_summary(project: Project) -> Dict[str, Any]:
    review = get_artifact(project, "review_report") or {}
    score_raw = get_artifact(project, "script_score_report") or {}
    polish = get_artifact(project, "polish_log") or {}

    scripts_ready = _scripts_fully_generated(project)

    status = "idle"
    if scripts_ready:
        if project.execution_status == Project.STATUS_RUNNING:
            status = "running"
        elif review or score_raw.get("overallScore") is not None or project.overall_score is not None:
            status = "done"
        else:
            status = "pending"

    pacing = review.get("pacing") if isinstance(review.get("pacing"), dict) else {}

    review_block: Optional[dict] = None
    if review:
        plot_structure = review.get("plotStructure") if isinstance(review.get("plotStructure"), dict) else {}
        quality_guard = review.get("qualityGuard") if isinstance(review.get("qualityGuard"), dict) else {}
        score_quick = review.get("scoreQuick") if isinstance(review.get("scoreQuick"), dict) else {}
        review_block = {
            "passed": review.get("passed"),
            "pacingPassed": pacing.get("passed"),
            "gatePassed": review.get("gatePassed"),
            "plotStructure": {
                "passed": plot_structure.get("passed"),
                "assessments": list(plot_structure.get("assessments") or [])[:4],
                "issues": list(plot_structure.get("issues") or [])[:4],
            }
            if plot_structure
            else None,
            "qualityGuard": {
                "passed": quality_guard.get("passed"),
                "skipped": quality_guard.get("skipped"),
                "assessments": list(quality_guard.get("assessments") or [])[:4],
                "issues": list(quality_guard.get("issues") or [])[:4],
                "totalDeductionPoints": quality_guard.get("totalDeductionPoints"),
                "predictedScore": quality_guard.get("predictedScore"),
            }
            if quality_guard
            else None,
            "scoreQuick": {
                "skipped": score_quick.get("skipped"),
                "reason": score_quick.get("reason"),
                "overallScore": score_quick.get("overallScore"),
                "grade": score_quick.get("grade"),
            }
            if score_quick
            else None,
            "complianceFuse": review.get("complianceFuse") if isinstance(review.get("complianceFuse"), dict) else None,
            "complianceContent": review.get("complianceContent") if isinstance(review.get("complianceContent"), dict) else None,
            "issues": [str(i) for i in (review.get("issues") or [])][:8],
            "executionRun": _latest_run_block(project, "review"),
        }
        review_block = portal_sanitize_review_block(review_block)
        review_block = portal_strip_agent_block(review_block)

    score_block: Optional[dict] = None
    overall = score_raw.get("overallScore")
    if overall is None:
        overall = project.overall_score
    grade = score_raw.get("grade") or project.grade
    if overall is not None or grade:
        score_block = {
            "overallScore": overall,
            "grade": grade or "",
            "executionRun": _latest_run_block(project, "score"),
        }
        score_block = portal_strip_agent_block(score_block)

    polish_block = _safe_polish_summary(polish)
    if polish_block:
        polish_block["executionRun"] = _latest_run_block(project, "polish")
        polish_block = portal_strip_agent_block(polish_block)

    insight_raw = get_artifact(project, "insight_report") or {}
    insight_run = _latest_run_block(project, "insight")
    insight_block = _safe_insight_summary(insight_raw)
    insight_has_content = bool(insight_block)
    if insight_block:
        insight_block["executionRun"] = insight_run
        insight_block = portal_strip_agent_block(insight_block)
    insight_status = _optional_node_status(insight_run, insight_has_content)

    marketing_raw = get_artifact(project, "marketing_kit") or {}
    marketing_run = _latest_run_block(project, "marketing")
    marketing_block = _safe_marketing_summary(marketing_raw)
    marketing_has_content = bool(
        marketing_block
        and (
            marketing_block.get("titles")
            or marketing_block.get("clipHooks")
            or marketing_block.get("posterSlogans")
        )
    )
    if marketing_has_content:
        marketing_block["executionRun"] = marketing_run
        marketing_block = portal_strip_agent_block(marketing_block)
    else:
        marketing_block = None
    marketing_status = _optional_node_status(marketing_run, marketing_has_content)

    return {
        "status": status,
        "scriptsReady": scripts_ready,
        "review": review_block,
        "score": score_block,
        "polish": polish_block or None,
        "insight": insight_block or None,
        "insightStatus": insight_status,
        "insightCanGenerate": scripts_ready and insight_status in ("not_run", "failed"),
        "marketing": marketing_block,
        "marketingStatus": marketing_status,
        "marketingCanGenerate": scripts_ready and marketing_status in ("not_run", "failed"),
        "chain": _build_post_script_chain_display(),
    }
