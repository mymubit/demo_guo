# -*- coding: utf-8 -*-
"""Tier4 分区中文标签（技能规则库后台展示）。"""
from __future__ import annotations

TIER4_SECTION_LABELS = {
    "_meta": "元信息",
    "p0_categories": "P0 熔断红线",
    "p1_categories": "P1 强制修改",
    "p2_advisories": "P2 建议优化",
    "nine_dimension_risk_assessment": "九维风险评估",
    "justice_tail_rule": "正义收束规则",
    "values_bottom_line": "价值观底线",
    "title_compliance_rules": "片名合规",
    "originality_rules": "原创性规则",
    "fuse_behavior": "熔断行为",
    "platform_specific": "平台专项",
    "new_2026_p0_items": "2026 P0 新增",
    "shortdramas_platform_quantitative": "短剧平台量化",
    "three_phase_compliance_checklist": "三阶段合规清单",
}

TIER4_SECTION_KEYS = list(TIER4_SECTION_LABELS.keys())


def tier4_section_label(section_key: str) -> str:
    key = (section_key or "").strip()
    return TIER4_SECTION_LABELS.get(key, key)
