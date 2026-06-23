# -*- coding: utf-8 -*-
"""
Tier1 分区种子 — drama.* 新体系。

旧的 brief/structure/character/outline/script 等 Agent 的 Tier1 映射已移除。
现在改为 drama.* agent_id → Tier1 区块名 的映射。

Tier1 区块定义：参见 drama-skills/knowledge/knowledge-sections.md
"""
from __future__ import annotations

# drama.* Agent → Tier1 知识区块映射
AGENT_TIER1_SEED: dict[str, list[str]] = {
    # 战略选题部
    "drama.topic-planner": ["philosophy"],
    "drama.market-analyst": ["rhythm_rules", "philosophy", "scoring", "episode_structure"],

    # 世界构建部
    "drama.world-architect": ["philosophy"],
    "drama.character-designer": ["philosophy", "foreshadowing_rules"],

    # 剧情引擎部
    "drama.plot-architect": [
        "episode_structure",
        "rhythm_rules",
        "quantitative_constraints",
        "foreshadowing_rules",
        "qdn_emotion_model",
        "hook_effectiveness",
        "payment_checkpoint_3card",
    ],
    "drama.narrative-engineer": [
        "episode_emotion_8nodes",
        "qdn_emotion_model",
        "hook_effectiveness",
        "emotion_externalization_dict",
        "episode_structure",
        "rhythm_rules",
        "foreshadowing_rules",
    ],

    # 创作执行部
    "drama.script-writer": [
        "episode_structure",
        "quantitative_constraints",
        "writing_prohibitions",
        "writing_requirements",
        "information_asymmetry_mechanics",
        "emotion_externalization_dict",
        "ai_tone_forbidden",
        "qdn_emotion_model",
        "format_standard",
        "hook_effectiveness",
        "episode_emotion_8nodes",
        "dialogue_quality",
    ],
    "drama.polish-master": [
        "writing_prohibitions",
        "writing_requirements",
        "ai_tone_forbidden",
        "emotion_externalization_dict",
        "dialogue_quality",
        "rhythm_rules",
        "quantitative_constraints",
        "format_standard",
    ],

    # 评审质控部
    "drama.script-reviewer": ["scoring", "format_standard"],
    "drama.quality-reporter": ["scoring"],

    # 制作宣发部
    "drama.production-pack": [
        "format_standard",
        "dialogue_quality",
        "hook_effectiveness",
        "scoring",
        "foreshadowing_rules",
    ],

    # 合规总编室
    "drama.compliance-guard": ["scoring"],
}

# NODE_TIER1_SEED: 节点级映射（与 agent 映射对齐）
NODE_TIER1_SEED: dict[str, list[str]] = {
    f"node_{k.replace('drama.', '').replace('-', '_')}": v
    for k, v in AGENT_TIER1_SEED.items()
}

DEFAULT_TIER1_SECTIONS_BY_AGENT = AGENT_TIER1_SEED
DEFAULT_TIER1_SECTIONS_BY_NODE = NODE_TIER1_SEED


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


def resolve_tier1_sections(node_id: str) -> list[str]:
    """按 drama.* agent_id 或 legacy node_id 解析 Tier1 区块。"""
    key = (node_id or "").strip()
    if key in AGENT_TIER1_SEED:
        return AGENT_TIER1_SEED[key]
    return NODE_TIER1_SEED.get(key, [])
