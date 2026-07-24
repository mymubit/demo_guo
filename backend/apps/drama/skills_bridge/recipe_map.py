# -*- coding: utf-8 -*-
"""V3 命令 → drama-skills 配方映射。"""
from __future__ import annotations

COMMAND_RECIPES: dict[str, dict] = {
    "generate_topic_brief": {
        "recipe_id": "create-project-brief",
        "role": "drama-topic-director",
        "writes": ["project_brief"],
        "requires_committed": [],
    },
    "generate_blueprint": {
        "recipe_id": "compose-story-bible",
        "role": "drama-story-bible",
        "writes": [
            "story_bible",
            "character_system",
            "world_system",
            "emotion_system",
            "originality_report",
        ],
        "requires_committed": ["project_brief"],
    },
    "generate_episode_plan": {
        "recipe_id": "design-episode-plan",
        "role": "drama-episode-designer",
        "writes": ["episode_plan"],
        "requires_committed": ["project_brief", "story_bible"],
    },
    "revise_episode_plan": {
        "recipe_id": "revise-episode-plan",
        "role": "drama-episode-designer",
        "writes": ["episode_plan"],
        "requires_committed": ["episode_plan"],
    },
    "write_episode_batch": {
        "recipe_id": "write-episodes",
        "role": "drama-script-writer",
        "writes": ["episode_scripts", "memory_checkpoint"],
        "requires_committed": ["episode_plan", "story_bible", "project_brief"],
    },
    "score_quality": {
        "recipe_id": "score-script",
        # skills 真相：roles/drama-script-scorer（plan 写 drama-score-critic 已偏离）
        "role": "drama-script-scorer",
        "writes": ["quality_report"],
        "requires_committed": ["episode_scripts", "episode_plan", "project_brief"],
        "commit_mode": "direct",
    },
    "check_compliance": {
        "recipe_id": "check-compliance",
        "role": "drama-compliance-guard",
        "writes": ["compliance_report"],
        "requires_committed": ["episode_scripts", "episode_plan", "project_brief"],
        "commit_mode": "direct",
    },
    "revise_from_findings": {
        "recipe_id": "revise-script",
        "role": "drama-revision-master",
        "writes": ["episode_scripts", "memory_checkpoint"],
        "requires_committed": ["episode_scripts", "episode_plan", "story_bible"],
        "commit_mode": "candidate",
    },
    "prepare_delivery": {
        "recipe_id": "prepare-delivery",
        "role": "drama-delivery-tool",
        "writes": ["production_package"],
        "requires_committed": ["episode_scripts", "quality_report", "compliance_report"],
        "commit_mode": "direct",
        "requires_delivery_gate": True,
    },
    # 独立剧本评审：复用 scorer/compliance 配方，不写项目 artifact
    "score_external_script": {
        "recipe_id": "score-script",
        "role": "drama-script-scorer",
        "writes": ["quality_report"],
        "requires_committed": [],
        "commit_mode": "none",
    },
    "check_external_compliance": {
        "recipe_id": "check-compliance",
        "role": "drama-compliance-guard",
        "writes": ["compliance_report"],
        "requires_committed": [],
        "commit_mode": "none",
    },
}


def recipe_for(command_type: str) -> dict:
    """返回命令对应的配方；未知命令抛出 KeyError。"""
    try:
        return dict(COMMAND_RECIPES[command_type])
    except KeyError as exc:
        raise KeyError(f"未知命令类型: {command_type}") from exc
