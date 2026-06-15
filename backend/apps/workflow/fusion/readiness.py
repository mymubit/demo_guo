# -*- coding: utf-8 -*-
"""按 fusion-plan §5 判定项目是否 ready（阈值来自 ReviewScoringConfig DB）。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from apps.skill.config.portal.review_scoring import ReviewScoringService


def evaluate_project_readiness(
    *,
    project_brief_confirmed: bool = False,
    has_structure: bool = False,
    has_characters: bool = False,
    has_outline: bool = False,
    all_episodes_gate_passed: bool = False,
    quality_final_verdict: Optional[str] = None,
    score_report: Optional[Dict[str, Any]] = None,
    compliance_fuse: bool = False,
) -> Dict[str, Any]:
    """输入为网站 DB 已聚合的布尔/报告对象，输出 ready 判定。"""
    scoring = ReviewScoringService.resolve()
    release_line = int(scoring["release_pass_score"])
    min_sub = int(scoring["min_sub_item_score"])

    overall = None
    eight_dim_ok = True
    dim_issues = []
    if score_report:
        overall = score_report.get("overallScore")
        dims = score_report.get("eightDimensionScores") or {}
        for key, block in dims.items():
            raw = (block or {}).get("rawScore")
            if raw is not None and raw < min_sub:
                eight_dim_ok = False
                dim_issues.append(f"{key}={raw}<{min_sub}")

    fuse_blocked = compliance_fuse
    gates_ok = (
        project_brief_confirmed
        and has_structure
        and has_characters
        and has_outline
        and all_episodes_gate_passed
        and (quality_final_verdict or "").lower() == "pass"
    )
    score_ok = (
        score_report is not None
        and overall is not None
        and overall >= release_line
        and eight_dim_ok
    )

    ready = gates_ok and score_ok and not fuse_blocked
    status = "ready" if ready else ("blocked" if fuse_blocked else "scoring" if gates_ok else "reviewing")

    skill_version = "unknown"
    try:
        from apps.workflow.fusion.config_loader import get_fusion_config

        skill_version = get_fusion_config().version
    except Exception:  # noqa: BLE001
        pass

    return {
        "ready": ready,
        "status": status,
        "release_pass_score": release_line,
        "min_sub_item_score": min_sub,
        "checks": {
            "project_brief_confirmed": project_brief_confirmed,
            "artifacts_complete": has_structure and has_characters and has_outline,
            "all_episodes_gate_passed": all_episodes_gate_passed,
            "quality_pass": (quality_final_verdict or "").lower() == "pass",
            "score_at_or_above_release": overall is not None and overall >= release_line,
            "eight_dimension_floor": eight_dim_ok,
            "no_compliance_fuse": not fuse_blocked,
        },
        "overall_score": overall,
        "dimension_issues": dim_issues,
        "skill_version": skill_version,
    }
