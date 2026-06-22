# -*- coding: utf-8 -*-
"""
Agent 计费规则 — drama.* 新体系。

每个 drama.* 角色对应的 Coin 消耗等级（1=最低，10=最高）。
旧的 brief/structure/outline/script 等已移除。
"""
from __future__ import annotations

from typing import Dict

# drama.* 角色 Coin 消耗等级（基于任务复杂度和 Token 消耗量）
DRAMA_AGENT_COIN_COST: Dict[str, int] = {
    # 战略选题部（轻量分析）
    "drama.market-radar": 2,
    "drama.formula-analyst": 2,
    "drama.topic-planner": 3,
    "drama.project-reviewer": 2,
    "drama.lapian-analyst": 5,

    # 世界构建部
    "drama.world-architect": 4,
    "drama.character-designer": 5,
    "drama.dream-analyst": 2,

    # 剧情引擎部
    "drama.emotion-architect": 3,
    "drama.plot-architect": 8,       # 大纲生成，Token消耗高
    "drama.hook-designer": 3,
    "drama.conflict-engine": 3,
    "drama.reversal-master": 3,
    "drama.rhythm-designer": 4,
    "drama.psychology-architect": 3,

    # 创作执行部（核心高消耗）
    "drama.script-writer": 15,       # 剧本写作，最高消耗
    "drama.dialogue-expert": 8,
    "drama.scene-director": 4,
    "drama.ip-adapter": 10,

    # 评审质控部
    "drama.script-reviewer": 5,
    "drama.reader-reviewer": 4,
    "drama.emotion-auditor": 4,
    "drama.quality-reporter": 6,

    # 修改润色部
    "drama.script-editor": 8,
    "drama.pacing-optimizer": 4,
    "drama.formatter": 2,
    "drama.word-governor": 2,
    "drama.style-guardian": 4,

    # 制作宣发部
    "drama.visual-producer": 5,
    "drama.storyboard-director": 6,
    "drama.post-processor": 4,
    "drama.marketing-officer": 4,

    # 合规总编室
    "drama.compliance-guard": 6,
    "drama.delivery-packer": 3,
    "drama.evolution-analyst": 4,
}

# 默认消耗（未在映射中的 agent）
DEFAULT_COIN_COST = 5


def get_agent_coin_cost(agent_id: str) -> int:
    """获取指定 drama.* Agent 的 Coin 消耗量。"""
    return DRAMA_AGENT_COIN_COST.get(agent_id, DEFAULT_COIN_COST)
