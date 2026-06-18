# -*- coding: utf-8 -*-
"""
Python-native world validation.
校验 structure-plan.worldview 块，直接从内存 dict 操作，无文件 I/O，无 Node 依赖。
"""
from __future__ import annotations

from typing import Any, Dict

from .result import ValidationResult

# 同步自 skill-thresholds.json
_DREAM_INDICATOR_KEYS = ("absoluteSafety", "efficientSatisfaction", "enhancedRealism")
_DREAM_INDICATOR_MIN = 6


def validate_world(structure_plan: Dict[str, Any]) -> ValidationResult:
    """
    校验 structure_plan.worldview 块。

    对应 JS: sub-world/index.js → validateWorldview(wv)
    """
    issues = _validate_worldview(structure_plan.get("worldview"))
    if issues:
        return ValidationResult.fail(issues, sub_skill="sub-world")
    return ValidationResult.ok(sub_skill="sub-world")


def _validate_worldview(wv: Any) -> list:
    issues = []

    if not wv:
        return ["缺少 worldview 块"]

    setting_summary = wv.get("settingSummary") or ""
    if len(setting_summary) < 5:
        issues.append("worldview.settingSummary 须 ≥5 字")

    root_rules = wv.get("rootRules")
    if not isinstance(root_rules, list) or len(root_rules) < 2:
        issues.append("worldview.rootRules 须至少 2 条")

    di = wv.get("dreamIndicators") or {}
    for key in _DREAM_INDICATOR_KEYS:
        val = di.get(key)
        if not isinstance(val, (int, float)) or val < _DREAM_INDICATOR_MIN:
            current = val if val is not None else "缺失"
            issues.append(
                f"worldview.dreamIndicators.{key} 建议 ≥{_DREAM_INDICATOR_MIN}（当前 {current}）"
            )

    return issues
