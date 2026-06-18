# -*- coding: utf-8 -*-
"""剧本质量维度文案与规则进化建议 — 单一数据源。"""
from __future__ import annotations

from typing import Dict

from apps.creation.models import ScriptQualityDimension

# 各维度对应的规则进化修改建议
QUALITY_DIMENSION_SUGGESTIONS: Dict[str, str] = {
    ScriptQualityDimension.HOOK: (
        "建议强化开场钩子模板，增加前 3 集开场吸引力检查点，并提高 hook 维度权重。"
    ),
    ScriptQualityDimension.EMOTION: (
        "建议增加情感曲线模板，强化情绪高点设置与 QDN 情绪匹配检查。"
    ),
    ScriptQualityDimension.REVERSAL: (
        "建议优化反转密度要求，在 Tier3 节点增加反转有效性校验。"
    ),
    ScriptQualityDimension.STRUCTURE: (
        "建议优化剧情结构模板，调整节奏分配与结构完整性检查阈值。"
    ),
    ScriptQualityDimension.COMPLIANCE: (
        "建议强化合规扫描规则，增加敏感词拦截阈值与合规维度权重。"
    ),
}

# 维度 → 目标技能 ID（规则进化提案定位）
QUALITY_DIMENSION_SKILL_MAP: Dict[str, str] = {
    ScriptQualityDimension.HOOK: "quality-hook",
    ScriptQualityDimension.EMOTION: "quality-emotion",
    ScriptQualityDimension.REVERSAL: "quality-reversal",
    ScriptQualityDimension.STRUCTURE: "quality-structure",
    ScriptQualityDimension.COMPLIANCE: "quality-compliance",
}

FALLBACK_SUGGESTION = "建议深入分析该维度的评分标准，适当调整规则阈值。"


def quality_dimension_label(dimension: str) -> str:
    """返回维度的中文标签；未知维度返回原值。"""
    try:
        return ScriptQualityDimension(dimension).label
    except ValueError:
        return dimension


def quality_dimension_suggestion(dimension: str) -> str:
    """返回维度对应的修改建议。"""
    return QUALITY_DIMENSION_SUGGESTIONS.get(dimension, FALLBACK_SUGGESTION)


def quality_dimension_skill_id(dimension: str) -> str:
    """返回维度关联的目标技能 ID。"""
    return QUALITY_DIMENSION_SKILL_MAP.get(dimension, f"quality-{dimension}" if dimension else "")
