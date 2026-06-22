# -*- coding: utf-8 -*-
"""
创作入口规划 — drama.* 新体系。

根据用户的创作入口类型，推荐对应的 drama.* 角色执行顺序。
旧的 from-scratch/from-novel/from-outline 逻辑已更新为 drama.* 体系。
"""
from __future__ import annotations

from typing import Any, Dict

from apps.agent.runtime import DRAMA_FAST_TRACK_AGENT_IDS


class DramaEntryPlan:
    """
    drama.* 创作入口规划。

    根据 track_mode（fast/expert）和创作起点类型，
    决定推荐的角色执行顺序。
    """

    # 快速通道：8个核心角色
    FAST_TRACK_PLAN = {
        "entry_type": "fast_track",
        "label": "快速通道",
        "description": "8个核心角色，适合初次创作和快速验证",
        "recommended_agents": DRAMA_FAST_TRACK_AGENT_IDS,
        "optional_agents": [],
    }

    # 专家通道：按部门分阶段
    EXPERT_TRACK_PLAN = {
        "entry_type": "expert_track",
        "label": "专家通道",
        "description": "36个专业角色，8个职能部门，适合商业精品项目",
        "phases": [
            {
                "phase": "strategy",
                "label": "战略选题",
                "agents": ["drama.market-radar", "drama.formula-analyst",
                           "drama.topic-planner", "drama.project-reviewer"],
            },
            {
                "phase": "worldbuilding",
                "label": "世界构建",
                "agents": ["drama.world-architect", "drama.character-designer",
                           "drama.dream-analyst"],
            },
            {
                "phase": "plot_design",
                "label": "剧情引擎",
                "agents": ["drama.emotion-architect", "drama.plot-architect",
                           "drama.hook-designer", "drama.conflict-engine",
                           "drama.reversal-master", "drama.rhythm-designer"],
            },
            {
                "phase": "writing",
                "label": "创作执行",
                "agents": ["drama.script-writer", "drama.dialogue-expert",
                           "drama.scene-director"],
            },
            {
                "phase": "review",
                "label": "评审质控",
                "agents": ["drama.script-reviewer", "drama.reader-reviewer",
                           "drama.emotion-auditor", "drama.quality-reporter"],
            },
            {
                "phase": "polish",
                "label": "修改润色",
                "agents": ["drama.script-editor", "drama.pacing-optimizer",
                           "drama.formatter", "drama.word-governor"],
            },
            {
                "phase": "production",
                "label": "制作宣发",
                "agents": ["drama.visual-producer", "drama.storyboard-director",
                           "drama.marketing-officer"],
            },
            {
                "phase": "compliance",
                "label": "合规交付",
                "agents": ["drama.compliance-guard", "drama.delivery-packer"],
            },
        ],
    }

    # IP改编专用入口
    IP_ADAPT_PLAN = {
        "entry_type": "ip_adapt",
        "label": "IP改编",
        "description": "小说/原著改编专用通道",
        "recommended_agents": [
            "drama.ip-adapter",
            "drama.world-architect",
            "drama.character-designer",
            "drama.plot-architect",
            "drama.script-writer",
            "drama.script-reviewer",
            "drama.quality-reporter",
            "drama.compliance-guard",
        ],
    }

    @classmethod
    def resolve(cls, track_mode: str = "fast", entry_type: str = "from-scratch") -> Dict[str, Any]:
        """
        根据创作模式和入口类型获取推荐的 Agent 执行计划。

        参数：
        - track_mode: "fast" | "expert"
        - entry_type: "from-scratch" | "from-novel" | "from-outline"
        """
        if entry_type == "from-novel":
            return cls.IP_ADAPT_PLAN

        if track_mode == "expert":
            return cls.EXPERT_TRACK_PLAN

        return cls.FAST_TRACK_PLAN
