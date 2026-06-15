# -*- coding: utf-8 -*-
"""Tier1 分区种子 — migrate / 磁盘 import / 后台「推荐预设」。"""

AGENT_TIER1_SEED: dict[str, list[str]] = {
    "brief": ["philosophy"],
    "world": [
        "philosophy",
        "rhythm_rules",
        "episode_structure",
        "episode_emotion_8nodes",
        "foreshadowing_rules",
        "scoring",
    ],
    "character": ["philosophy", "foreshadowing_rules"],
    "outline": [
        "episode_structure",
        "rhythm_rules",
        "quantitative_constraints",
        "foreshadowing_rules",
        "qdn_emotion_model",
        "hook_effectiveness",
        "payment_checkpoint_3card",
    ],
    "script": [
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
    "review": ["scoring"],
    "polish": [
        "writing_prohibitions",
        "writing_requirements",
        "ai_tone_forbidden",
        "emotion_externalization_dict",
        "dialogue_quality",
    ],
    "score": ["scoring"],
    "adapt": ["philosophy", "writing_prohibitions"],
    "insight": ["scoring", "hook_effectiveness", "foreshadowing_rules"],
    "emotion_architect": [
        "episode_emotion_8nodes",
        "qdn_emotion_model",
        "hook_effectiveness",
        "emotion_externalization_dict",
    ],
    "marketing": ["hook_effectiveness"],
}

NODE_TIER1_SEED: dict[str, list[str]] = {
    "node-1-input": AGENT_TIER1_SEED["brief"],
    "node-2-structure": AGENT_TIER1_SEED["world"],
    "node-3-character": AGENT_TIER1_SEED["character"],
    "node-4-outline": AGENT_TIER1_SEED["outline"],
    "node-5-script": AGENT_TIER1_SEED["script"],
    "node-6-review": AGENT_TIER1_SEED["review"],
    "node-7-polish": AGENT_TIER1_SEED["polish"],
    "node-8-score": AGENT_TIER1_SEED["score"],
    "node-9-adapt": AGENT_TIER1_SEED["adapt"],
    "node-10-insight": AGENT_TIER1_SEED["insight"],
    "node-11-marketing": AGENT_TIER1_SEED["marketing"],
}

DEFAULT_TIER1_SECTIONS_BY_NODE = NODE_TIER1_SEED
DEFAULT_TIER1_SECTIONS_BY_AGENT = AGENT_TIER1_SEED
