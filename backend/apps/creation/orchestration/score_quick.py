# -*- coding: utf-8 -*-
"""Python-native quick score preview."""
from __future__ import annotations

from typing import Any, Dict


def run_score_quick_preview(
    project,
    pipeline_result: dict,
    *,
    runner=None,
) -> Dict[str, Any]:
    existing = {}
    try:
        from ..artifact_service import get_artifact

        existing = get_artifact(project, "script_score_report") or get_artifact(project, "score_report") or {}
    except Exception:  # noqa: BLE001
        existing = {}
    overall = existing.get("overallScore") or getattr(project, "overall_score", None)
    grade = existing.get("grade") or getattr(project, "grade", "")
    return {
        "skipped": overall is None and not grade,
        "passed": True,
        "mode": "quick",
        "overallScore": overall,
        "grade": grade or "",
        "scorerPayload": existing,
        "source": "python-native",
    }
