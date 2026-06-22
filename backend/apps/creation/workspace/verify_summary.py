# -*- coding: utf-8 -*-
"""改编/参考创作复核摘要。"""
from __future__ import annotations

from typing import Any, Dict, List


def verify_summary(adaptation_meta: dict) -> Dict[str, Any]:
    reports = adaptation_meta.get("verifyReports") or {}
    brief = adaptation_meta.get("verifyCreation") or {}
    stages: List[Dict[str, Any]] = []
    labels = {
        "world_setting": "世界观",
        "character_bible": "人设",
        "series_outline": "大纲",
        "episode_scripts": "剧本",
    }
    if brief and not brief.get("skipped"):
        stages.append(
            {
                "key": "project_brief",
                "label": "立项简报校验",
                "passed": brief.get("passed"),
                "skipped": False,
            }
        )
    for key, label in labels.items():
        row = reports.get(key)
        if not isinstance(row, dict):
            continue
        stages.append(
            {
                "key": key,
                "label": label,
                "passed": row.get("passed"),
                "skipped": bool(row.get("skipped")),
                "issues": (row.get("issues") or [])[:3],
            }
        )
    failed = [s for s in stages if s.get("passed") is False and not s.get("skipped")]
    return {
        "stages": stages,
        "allPassed": len(stages) > 0 and len(failed) == 0,
        "hasReports": bool(stages),
        "failedCount": len(failed),
    }
