# -*- coding: utf-8 -*-
"""Compare score reports against internal S-grade baselines."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

_DATA_ROOT = Path(getattr(settings, "SCRIPT_FORGE_ASSET_ROOT", "")) / "data"
_CATALOG_PATH = _DATA_ROOT / "s-grade-catalog.json"
_S_GRADE_CACHE_DIR = _DATA_ROOT / "s-grade-scores"
_COMPARE_DIMENSIONS = [
    "dramaGene",
    "paymentCard",
    "structural",
    "detailPolish",
    "emotionalDesign",
]
_DIMENSION_LABELS = {
    "dramaGene": "Drama Gene",
    "paymentCard": "Payment Card",
    "structural": "Structure",
    "detailPolish": "Detail Polish",
    "emotionalDesign": "Emotional Design",
}


def _load_catalog() -> Dict[str, Any]:
    try:
        if _CATALOG_PATH.is_file():
            return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ScriptComparator] load catalog failed: %s", exc)
    return {}


def _load_s_grade_score(script_id: str) -> Optional[Dict[str, Any]]:
    path = _S_GRADE_CACHE_DIR / f"{script_id}-deep.json"
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ScriptComparator] load baseline score failed: %s", exc)
    return None


def _select_top_baselines(catalog: Dict[str, Any], genre: str, top_n: int = 3) -> List[Dict[str, Any]]:
    scripts = [
        s for s in (catalog.get("scripts") or [])
        if isinstance(s, dict) and s.get("grade") == "S" and s.get("enabled", True)
    ]
    scripts.sort(key=lambda s: 0 if s.get("genre") == genre else 1)
    baselines: List[Dict[str, Any]] = []
    for item in scripts[:top_n]:
        score = _load_s_grade_score(str(item.get("id") or ""))
        if not score:
            continue
        baselines.append(
            {
                "id": item.get("id"),
                "title": item.get("title") or "",
                "genre": item.get("genre") or "",
                "sameGenre": item.get("genre") == genre,
                **score,
            }
        )
    return baselines


def _extract_dimension_score(score_report: Dict[str, Any], dim_key: str) -> Optional[float]:
    raw = score_report.get(dim_key)
    if isinstance(raw, dict):
        raw = raw.get("score") or raw.get("value")
    if raw is None:
        dimensions = score_report.get("dimensions") or {}
        if isinstance(dimensions, dict):
            raw = dimensions.get(dim_key)
            if isinstance(raw, dict):
                raw = raw.get("score") or raw.get("value")
    try:
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _compute_gap(current_score: Optional[float], baseline_score: float) -> Dict[str, Any]:
    if current_score is None:
        return {"current": None, "gap": None, "status": "missing"}
    gap = round(float(current_score) - float(baseline_score), 1)
    if gap >= -3:
        status = "close"
    elif gap >= -8:
        status = "behind"
    else:
        status = "critical"
    return {"current": round(float(current_score), 1), "gap": gap, "status": status}


def _generate_priority_fixes(dimension_gaps: Dict[str, Any], genre: str) -> List[Dict[str, Any]]:
    items = []
    for key, gap in dimension_gaps.items():
        if gap.get("status") in {"behind", "critical", "missing"}:
            items.append(
                {
                    "dimension": key,
                    "label": _DIMENSION_LABELS.get(key, key),
                    "priority": "high" if gap.get("status") == "critical" else "medium",
                    "suggestions": _get_fix_suggestions(key, float(gap.get("gap") or -10), genre),
                }
            )
    return items


def _get_fix_suggestions(dim_key: str, gap: float, genre: str) -> List[str]:
    return [
        f"Strengthen { _DIMENSION_LABELS.get(dim_key, dim_key) } against internal baselines.",
        f"Re-run explicit review/score agents after changes for {genre or 'general'} genre.",
    ]


def run_script_comparator(project, *, genre: str = "", top_n: int = 3) -> Dict[str, Any]:
    from ..artifact_service import get_artifact, save_artifact

    score_report = get_artifact(project, "script_score_report") or get_artifact(project, "score_report") or {}
    if not genre:
        brief = get_artifact(project, "project_brief") or {}
        genre = brief.get("genre") or ""

    catalog = _load_catalog()
    if not catalog:
        return {"agentId": "script_comparator", "status": "skipped", "reason": "baseline catalog unavailable"}

    baselines = _select_top_baselines(catalog, genre, top_n=top_n)
    if not baselines:
        return {"agentId": "script_comparator", "status": "skipped", "reason": "no S-grade baselines"}

    current_final = score_report.get("finalScore") or score_report.get("overallScore")
    try:
        current_final = float(current_final) if current_final is not None else None
    except (TypeError, ValueError):
        current_final = None

    dimension_gaps: Dict[str, Any] = {}
    for dim_key in _COMPARE_DIMENSIONS:
        current_score = _extract_dimension_score(score_report, dim_key)
        baseline_scores = [
            value for value in (_extract_dimension_score(b, dim_key) for b in baselines) if value is not None
        ]
        if not baseline_scores:
            continue
        avg_baseline = sum(baseline_scores) / len(baseline_scores)
        gap = _compute_gap(current_score, avg_baseline)
        dimension_gaps[dim_key] = {
            "label": _DIMENSION_LABELS.get(dim_key, dim_key),
            "avgBaseline": round(avg_baseline, 1),
            **gap,
        }

    baseline_finals = [
        float(b.get("finalScore") or b.get("overallScore") or 0)
        for b in baselines
        if b.get("finalScore") is not None or b.get("overallScore") is not None
    ]
    avg_final = sum(baseline_finals) / len(baseline_finals) if baseline_finals else 0
    report = {
        "agentId": "script_comparator",
        "projectId": str(project.id),
        "genre": genre,
        "finalScore": {
            "current": round(current_final, 1) if current_final is not None else None,
            "avgBaseline": round(avg_final, 1),
            **_compute_gap(current_final, avg_final),
        },
        "dimensionGaps": dimension_gaps,
        "priorityFixes": _generate_priority_fixes(dimension_gaps, genre),
        "baselines": [{"id": b.get("id"), "title": b.get("title"), "sameGenre": b.get("sameGenre")} for b in baselines],
        "status": "completed",
    }
    save_artifact(project, "comparator_report", report)
    return report
