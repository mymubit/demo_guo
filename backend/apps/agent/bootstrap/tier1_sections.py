# -*- coding: utf-8 -*-
"""
Tier1 分区映射 — 数据来自 drama-skills/knowledge/knowledge-sections.md（Git SSOT）。

不再在后端硬编码 section 列表；文件缺失时返回空映射并打日志。
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

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
    "character_rules": "角色逻辑",
    "conflict_escalation": "冲突升级",
    "learned_rules": "经验规则 LR",
}


def get_agent_tier1_sections() -> dict[str, list[str]]:
    from apps.drama.skills_registry import load_agent_tier1_sections

    sections = load_agent_tier1_sections()
    if not sections:
        logger.warning("[tier1_sections] knowledge-sections.md 未解析到映射，Tier1 片段将为空")
    return sections


# 兼容旧 import 名；值为 SSOT 加载结果（非硬编码）
AGENT_TIER1_SEED: dict[str, list[str]] = {}


def _ensure_tier1_loaded() -> dict[str, list[str]]:
    global AGENT_TIER1_SEED
    if not AGENT_TIER1_SEED:
        AGENT_TIER1_SEED = get_agent_tier1_sections()
    return AGENT_TIER1_SEED


NODE_TIER1_SEED: dict[str, list[str]] = {}


def _ensure_node_tier1_loaded() -> dict[str, list[str]]:
    global NODE_TIER1_SEED
    if not NODE_TIER1_SEED:
        NODE_TIER1_SEED = {
            f"node_{agent_id.replace('drama.', '').replace('-', '_')}": sections
            for agent_id, sections in _ensure_tier1_loaded().items()
        }
    return NODE_TIER1_SEED


DEFAULT_TIER1_SECTIONS_BY_AGENT = AGENT_TIER1_SEED
DEFAULT_TIER1_SECTIONS_BY_NODE = NODE_TIER1_SEED


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
    agent_sections = _ensure_tier1_loaded()
    if key in agent_sections:
        return agent_sections[key]
    return _ensure_node_tier1_loaded().get(key, [])
