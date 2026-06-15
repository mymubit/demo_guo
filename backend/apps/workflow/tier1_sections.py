# -*- coding: utf-8 -*-
"""Tier1 分区 — 运行时解析与后台 catalog（种子在 bootstrap.tier1_sections）。"""
from apps.agent.bootstrap.tier1_sections import (
    AGENT_TIER1_SEED,
    DEFAULT_TIER1_SECTIONS_BY_AGENT,
    DEFAULT_TIER1_SECTIONS_BY_NODE,
    NODE_TIER1_SEED,
)

TIER1_SECTION_LABELS = {
    "philosophy": "创作哲学",
    "rhythm_rules": "节奏规则",
    "episode_structure": "分集结构",
    "quantitative_constraints": "量化约束",
    "writing_prohibitions": "写作禁止项",
    "writing_requirements": "写作要求",
    "foreshadowing_rules": "伏笔规则",
    "qdn_emotion_model": "QDN 情绪模型",
    "scoring": "评分规则",
    "format_standard": "格式标准",
    "information_asymmetry_mechanics": "信息差机制",
    "emotion_externalization_dict": "情感外化词典",
    "ai_tone_forbidden": "AI 腔禁止",
    "hook_effectiveness": "钩子有效性",
    "episode_emotion_8nodes": "分集情绪八节点",
    "payment_checkpoint_3card": "付费卡点三卡",
    "dialogue_quality": "对话质量",
}


def tier1_section_label(section_key: str) -> str:
    key = (section_key or "").strip()
    return TIER1_SECTION_LABELS.get(key, key)


def tier1_section_catalog_detail() -> list:
    from apps.skill.skills.loader import _TIER1_RENDERERS

    return [
        {"key": key, "label": tier1_section_label(key)}
        for key in sorted(_TIER1_RENDERERS.keys())
    ]


def resolve_tier1_sections(node_id: str) -> list:
    from apps.agent.binding import resolve_tier1_sections_for_node

    return resolve_tier1_sections_for_node(node_id)
