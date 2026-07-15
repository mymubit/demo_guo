# -*- coding: utf-8 -*-
"""质检门禁判定。"""
from __future__ import annotations

from typing import Any

from apps.drama.services.skills_loader import get_skills_loader


def quality_gate_passed(
    quality_report: dict[str, Any],
    compliance_report: dict[str, Any],
) -> bool:
    """根据 skills SSOT 阈值判断是否通过质检。"""
    loader = get_skills_loader()
    scoring = loader.load_seed_yaml("foundation/constraints/quality-scoring.yaml")
    threshold = float((scoring.get("grade_thresholds") or {}).get("B", 75))
    score = float(quality_report.get("overall_score", 0))
    blocking = compliance_report.get("blocking_issues") or []
    if score < threshold:
        return False
    if blocking:
        return False
    return True
