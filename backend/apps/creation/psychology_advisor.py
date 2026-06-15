# -*- coding: utf-8 -*-
"""psychology-advisor：受众心理策略（规则层，并入 creativePlan）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from apps.skill.config.portal.theme_templates import ThemeTemplateCatalogService

from .industry_benchmarks import reversal_cadence


_THEME_PSYCHOLOGY = {
    "family-revenge": {
        "dominantArchetype": "catharsis",
        "auxiliaryArchetypes": ["compensation", "confirmation"],
        "audiencePainPoint": "长期压抑后的情绪宣泄与正义兑现",
        "informationGapStrategy": "隐藏证据/身份分批揭露，每10集放大信息差",
        "satisfactionRhythm": "虐3集→小爽1集→大爽每10集",
    },
    "overbearing-ceo": {
        "dominantArchetype": "projection",
        "auxiliaryArchetypes": ["efficient-satisfaction", "confirmation"],
        "audiencePainPoint": "被看不起后的身份反转与阶层跃迁幻想",
        "informationGapStrategy": "女主真实身份分层曝光，反派持续误判",
        "satisfactionRhythm": "羞辱铺垫→小打脸→身份揭露大高潮",
    },
    "sweet-pet": {
        "dominantArchetype": "escape",
        "auxiliaryArchetypes": ["confirmation", "compensation"],
        "audiencePainPoint": "情感安全感与追妻火葬场补偿",
        "informationGapStrategy": "误会链+童年真相延后揭晓",
        "satisfactionRhythm": "甜15集→虐20集→追妻25集→合10集",
    },
    "time-travel": {
        "dominantArchetype": "compensation",
        "auxiliaryArchetypes": ["catharsis", "efficient-satisfaction"],
        "audiencePainPoint": "改写命运、提前复仇的掌控感",
        "informationGapStrategy": "重生者预知 vs 反派蒙在鼓里",
        "satisfactionRhythm": "改命小胜→宿敌反扑→终极清算",
    },
    "suspense": {
        "dominantArchetype": "confirmation",
        "auxiliaryArchetypes": ["escape", "projection"],
        "audiencePainPoint": "悬念解谜与认知反转快感",
        "informationGapStrategy": "多视角信息差，真相延后集中引爆",
        "satisfactionRhythm": "埋钩→误导→揭底三连击",
    },
    "healing": {
        "dominantArchetype": "resonance",
        "auxiliaryArchetypes": ["confirmation", "compensation"],
        "audiencePainPoint": "都市压力人群的职场焦虑/情感创伤/自我认同困境，渴望被理解与释怀",
        "informationGapStrategy": "不靠信息差爽点，靠真实痛点共鸣建立代入；情绪在结尾给正向出口",
        "satisfactionRhythm": "痛点共鸣→被理解时刻（每10集）→心理修复节点（每15集）→温暖出口，禁大起大落与说教",
    },
}


def _theme_templates() -> dict:
    return ThemeTemplateCatalogService.get_templates_map()


def build_psychology_strategy(
    *,
    theme: str = "",
    project_brief: Optional[dict] = None,
    structure_plan: Optional[dict] = None,
    total_episodes: int = 80,
) -> Dict[str, Any]:
    theme_code = (theme or "").strip() or "mixed-theme"
    brief = project_brief if isinstance(project_brief, dict) else {}
    theme_code = (brief.get("theme") or theme_code).strip() or "mixed-theme"

    base = dict(_THEME_PSYCHOLOGY.get(theme_code) or _THEME_PSYCHOLOGY.get("overbearing-ceo") or {})
    if theme_code not in _THEME_PSYCHOLOGY:
        base.setdefault("dominantArchetype", "efficient-satisfaction")
        base.setdefault("auxiliaryArchetypes", ["compensation"])
        base.setdefault("audiencePainPoint", "高频爽点与情绪释放")
        base.setdefault("informationGapStrategy", "主角底牌分层揭露")
        base.setdefault("satisfactionRhythm", "每3集小波动，每10集大高潮")

    tmpl = _theme_templates().get(theme_code) or ThemeTemplateCatalogService.get_theme_entry(theme_code) or {}
    if tmpl.get("audienceFit") and not brief.get("audiencePainPoint"):
        base["audienceFit"] = str(tmpl.get("audienceFit"))[:200]
    if tmpl.get("coreConflictFormula"):
        base["coreConflictFormula"] = str(tmpl.get("coreConflictFormula"))[:300]

    cadence = reversal_cadence()
    dream_layers: List[dict] = [
        {"level": "surface", "label": "表层爽点", "notes": base.get("satisfactionRhythm", "")},
        {
            "level": "gap",
            "label": "信息差",
            "notes": base.get("informationGapStrategy", ""),
        },
        {
            "level": "cadence",
            "label": "反转节奏",
            "notes": f"{cadence.get('small')} / {cadence.get('medium')}",
        },
    ]

    rev_count = 0
    if isinstance(structure_plan, dict):
        rev_count = len(structure_plan.get("keyReversalPoints") or [])

    notes_parts = [
        f"全剧{int(total_episodes or 80)}集",
        base.get("audiencePainPoint", ""),
        cadence.get("note", ""),
    ]
    if rev_count:
        notes_parts.append(f"结构规划含 {rev_count} 个反转锚点")

    return {
        **base,
        "dreamLayers": dream_layers,
        "notes": "；".join(p for p in notes_parts if p)[:500],
        "source": "psychology-advisor-rule",
    }


def merge_psychology_into_creative_plan(
    creative_plan: dict,
    *,
    theme: str = "",
    project_brief: Optional[dict] = None,
    structure_plan: Optional[dict] = None,
    total_episodes: int = 80,
) -> dict:
    out = dict(creative_plan or {})
    existing = out.get("psychologyStrategy")
    if isinstance(existing, dict) and (existing.get("dominantArchetype") or (existing.get("notes") or "").strip()):
        if existing.get("dreamLayers") or existing.get("informationGapStrategy"):
            return out
    out["psychologyStrategy"] = build_psychology_strategy(
        theme=theme,
        project_brief=project_brief,
        structure_plan=structure_plan,
        total_episodes=total_episodes,
    )
    return out
