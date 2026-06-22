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
    "drama.market-radar": ["rhythm_rules"],       # 市场分析，节奏规则用于趋势判断
    "drama.formula-analyst": ["philosophy"],
    "drama.topic-planner": ["philosophy"],
    "drama.project-reviewer": ["scoring", "philosophy"],
    "drama.lapian-analyst": ["rhythm_rules", "episode_structure"],

    # 世界构建部
    "drama.world-architect": ["philosophy"],
    "drama.character-designer": ["philosophy", "foreshadowing_rules"],
    "drama.dream-analyst": ["scoring"],

    # 剧情引擎部
    "drama.emotion-architect": ["episode_emotion_8nodes", "qdn_emotion_model",
                                 "hook_effectiveness", "emotion_externalization_dict"],
    "drama.plot-architect": ["episode_structure", "rhythm_rules",
                              "quantitative_constraints", "foreshadowing_rules",
                              "qdn_emotion_model", "hook_effectiveness",
                              "payment_checkpoint_3card"],
    "drama.hook-designer": ["hook_effectiveness", "episode_emotion_8nodes"],
    "drama.conflict-engine": ["episode_structure", "rhythm_rules"],
    "drama.reversal-master": ["foreshadowing_rules", "hook_effectiveness"],
    "drama.rhythm-designer": ["rhythm_rules", "episode_structure",
                               "qdn_emotion_model", "episode_emotion_8nodes"],
    "drama.psychology-architect": ["qdn_emotion_model", "hook_effectiveness",
                                    "emotion_externalization_dict"],

    # 创作执行部
    "drama.script-writer": ["episode_structure", "quantitative_constraints",
                             "writing_prohibitions", "writing_requirements",
                             "information_asymmetry_mechanics",
                             "emotion_externalization_dict", "ai_tone_forbidden",
                             "qdn_emotion_model", "format_standard",
                             "hook_effectiveness", "episode_emotion_8nodes",
                             "dialogue_quality"],
    "drama.dialogue-expert": ["writing_prohibitions", "writing_requirements",
                               "ai_tone_forbidden", "emotion_externalization_dict",
                               "dialogue_quality"],
    "drama.scene-director": ["format_standard", "quantitative_constraints"],
    "drama.ip-adapter": ["philosophy", "writing_prohibitions"],

    # 评审质控部
    "drama.script-reviewer": ["scoring", "format_standard"],
    "drama.reader-reviewer": ["scoring", "hook_effectiveness"],
    "drama.emotion-auditor": ["episode_emotion_8nodes", "qdn_emotion_model"],
    "drama.quality-reporter": ["scoring"],

    # 修改润色部
    "drama.script-editor": ["writing_prohibitions", "writing_requirements",
                             "ai_tone_forbidden", "emotion_externalization_dict",
                             "dialogue_quality"],
    "drama.pacing-optimizer": ["rhythm_rules", "quantitative_constraints"],
    "drama.formatter": ["format_standard"],
    "drama.word-governor": ["quantitative_constraints"],
    "drama.style-guardian": ["dialogue_quality", "writing_requirements"],

    # 制作宣发部
    "drama.visual-producer": ["format_standard"],
    "drama.storyboard-director": ["format_standard"],
    "drama.post-processor": ["format_standard", "dialogue_quality"],  # 配音/字幕后期处理
    "drama.marketing-officer": ["hook_effectiveness"],

    # 合规总编室
    "drama.compliance-guard": ["scoring"],
    "drama.delivery-packer": ["scoring", "format_standard"],
    "drama.evolution-analyst": ["scoring", "hook_effectiveness", "foreshadowing_rules"],
}

# NODE_TIER1_SEED: 节点级映射（与 agent 映射对齐）
NODE_TIER1_SEED: dict[str, list[str]] = {
    f"node_{k.replace('drama.', '').replace('-', '_')}": v
    for k, v in AGENT_TIER1_SEED.items()
}

DEFAULT_TIER1_SECTIONS_BY_AGENT = AGENT_TIER1_SEED
DEFAULT_TIER1_SECTIONS_BY_NODE = NODE_TIER1_SEED


def resolve_tier1_sections(agent_id: str) -> list[str]:
    """获取指定 drama.* Agent 的 Tier1 区块列表。"""
    return AGENT_TIER1_SEED.get(agent_id, [])
