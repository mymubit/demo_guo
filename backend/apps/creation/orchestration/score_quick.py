# -*- coding: utf-8 -*-
"""Review 阶段 score-quick 快评。"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def run_score_quick_preview(
    project,
    pipeline_result: dict,
    *,
    runner=None,
) -> Dict[str, Any]:
    """调用 sub-score --mode=quick，不覆盖 script_score_report。"""
    if not getattr(settings, "FUSION_SKILL_ENABLED", True):
        return {"skipped": True, "reason": "FUSION_SKILL_ENABLED=false", "passed": True}

    from ..artifact_service import get_artifact
    from ..fusion.fusion_pipeline import _prepare_script_markdown
    from .sub_skill_runner import cli_score_quick, unwrap_fusion_cli_result

    try:
        script_path, score_out, markdown = _prepare_script_markdown(project, pipeline_result)
    except ValueError as exc:
        return {"skipped": True, "reason": str(exc), "passed": True}

    if not markdown.strip():
        return {"skipped": True, "reason": "无剧本文本", "passed": True}

    if runner is None:
        from apps.workflow.fusion import FusionCliRunner, get_fusion_config

        runner = FusionCliRunner(get_fusion_config())

    work_dir = score_out.parent
    brief_path = work_dir / f"{project.id.hex}_brief_quick.json"
    brief = get_artifact(project, "project_brief") or {}
    brief_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")

    quick_out = work_dir / f"{project.id.hex}_score_quick.json"
    try:
        raw = cli_score_quick(
            runner,
            script_path,
            bridge=True,
            output_path=quick_out,
            brief_path=brief_path,
        )
        payload = unwrap_fusion_cli_result(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[ReviewAgent] score-quick failed: %s", exc)
        return {"skipped": False, "passed": True, "warning": str(exc)[:200]}

    bridge_path = quick_out.parent / f"{quick_out.stem}.eight-dim.json"
    eight_dim: Optional[dict] = None
    if bridge_path.is_file():
        try:
            eight_dim = json.loads(bridge_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            eight_dim = None

    score_json = payload if isinstance(payload, dict) else {}
    overall = None
    grade = ""
    if eight_dim:
        overall = eight_dim.get("overallScore")
        grade = eight_dim.get("grade") or ""
    else:
        overall = score_json.get("finalScore") or score_json.get("overallScore")
        grade = score_json.get("grade") or ""

    return {
        "skipped": False,
        "passed": True,
        "mode": "quick",
        "overallScore": overall,
        "grade": grade,
        "scorerPayload": score_json,
        "eightDimPreview": eight_dim,
        "outputPath": str(quick_out),
    }
