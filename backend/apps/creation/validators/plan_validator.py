# -*- coding: utf-8 -*-
"""
Python-native plan validation.
校验 series_outline.creativePlan 块，直接从内存 dict 操作，无文件 I/O，无 Node 依赖。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .result import ValidationResult

# 同步自 skill-thresholds.json
_PAY_MIN_EPISODES = 30
_PAY_WINDOW = (8, 9, 10)


def validate_plan(
    series_outline: Dict[str, Any],
    *,
    expected_episodes: Optional[int] = None,
) -> ValidationResult:
    """
    校验 series_outline 的 creativePlan 与逐集结构。

    对应 JS: sub-plan/index.js → validateCreativePlan(outline)
    """
    issues = _validate_creative_plan(series_outline, expected_episodes=expected_episodes)
    if issues:
        return ValidationResult.fail(issues, sub_skill="sub-plan")
    return ValidationResult.ok(sub_skill="sub-plan")


def _validate_creative_plan(outline: Dict[str, Any], *, expected_episodes: Optional[int]) -> list:
    issues = []

    total = int(expected_episodes or outline.get("totalEpisodes") or 0)
    cp = outline.get("creativePlan")

    if not cp:
        return ["缺少 creativePlan 块"]

    hook_diversity = cp.get("hookDiversity") or {}
    if not isinstance(hook_diversity.get("requiredTypes"), list) or not hook_diversity["requiredTypes"]:
        issues.append("creativePlan.hookDiversity.requiredTypes 不能为空")

    if total >= _PAY_MIN_EPISODES:
        checkpoints = cp.get("paymentCheckpoints") or []
        if len(checkpoints) < 2:
            issues.append(f"≥{_PAY_MIN_EPISODES}集须配置 paymentCheckpoints（建议第8-10集）")
        covered = [ep for ep in _PAY_WINDOW if any(c.get("episode") == ep for c in checkpoints)]
        if len(covered) < 2:
            issues.append(
                f"第 {'、'.join(str(e) for e in _PAY_WINDOW)} 集窗口须至少覆盖 2 集付费/强卡点"
            )

    episodes = outline.get("episodes") or []
    first_10 = episodes[:10]
    missing_hook_code = sum(1 for ep in first_10 if not ep.get("hookTypeCode"))
    if missing_hook_code > 5:
        issues.append("前10集多数缺少 hookTypeCode，请对照 hook-types-library 标注")

    reversal_schedule = cp.get("reversalSchedule")
    if not isinstance(reversal_schedule, list) or not reversal_schedule:
        issues.append("creativePlan.reversalSchedule 建议至少 1 条全剧反转排期")

    return issues
