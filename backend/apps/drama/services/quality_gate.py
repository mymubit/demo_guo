# -*- coding: utf-8 -*-
"""质检门禁判定。"""
from __future__ import annotations

from typing import Any

from django.conf import settings

from apps.drama.services.skills_loader import get_skills_loader


def grade_b_threshold() -> float:
    """B 档分数线（skills SSOT）。"""
    loader = get_skills_loader()
    scoring = loader.load_seed_yaml("foundation/constraints/quality-scoring.yaml")
    return float((scoring.get("grade_thresholds") or {}).get("B", 75))


def quality_score_meets_threshold(quality_report: dict[str, Any]) -> bool:
    """评分是否达到可进入合规的阈值（默认 B 档）。"""
    score = float(quality_report.get("overall_score", 0) or 0)
    return score >= grade_b_threshold()


def quality_gate_passed(
    quality_report: dict[str, Any],
    compliance_report: dict[str, Any],
) -> bool:
    """根据 skills SSOT 阈值判断是否通过质检。"""
    threshold = grade_b_threshold()
    score = float(quality_report.get("overall_score", 0))
    blocking = compliance_report.get("blocking_issues") or []
    if score < threshold:
        return False
    if blocking:
        return False
    return True


def prefer_parallel_quality_judges(
    *,
    request_payload: dict[str, Any] | None = None,
    project_settings: dict[str, Any] | None = None,
) -> bool:
    """是否并行跑评分+合规。默认 False（串行：先评分，达标再合规）。

    开启顺序：Django 设置 DRAMA_QUALITY_JUDGES_PARALLEL →
    request_payload.parallel_quality_judges →
    creation_preferences.parallel_quality_judges。
    """
    if getattr(settings, "DRAMA_QUALITY_JUDGES_PARALLEL", False):
        return True
    payload = request_payload or {}
    if "parallel_quality_judges" in payload:
        return bool(payload.get("parallel_quality_judges"))
    prefs = (project_settings or {}).get("creation_preferences") or {}
    return bool(prefs.get("parallel_quality_judges"))


def skipped_compliance_report(
    *,
    overall_score: float,
    threshold: float,
    resolved_script_key: str = "episode_scripts",
) -> dict[str, Any]:
    """评分未达标时的占位合规报告（满足 schema，标明跳过原因）。"""
    key = resolved_script_key
    if key not in {"episode_scripts", "external_script"}:
        key = "episode_scripts"
    return {
        "drama_title": "（评分未达标，合规已跳过）",
        "check_mode": "standard",
        "target_platform": "generic",
        "platform_policy_version": None,
        "platform_policy_verified_at": None,
        "checked_artifact": "latest_script",
        "resolved_script_key": key,
        "overall_result": "风险",
        "blocking_issues": [],
        "risk_items": [
            {
                "type": "p2",
                "description": (
                    f"因评分 {overall_score:g} 未达 B 档阈值 {threshold:g}，"
                    "本轮跳过合规检查以节省调用。"
                ),
                "suggestion": (
                    "先按评分报告修复后再重跑质检；"
                    "若需始终并行评分与合规，打开 "
                    "creation_preferences.parallel_quality_judges。"
                ),
            }
        ],
    }
