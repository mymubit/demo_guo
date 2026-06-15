# -*- coding: utf-8 -*-
"""conflict-advisor：危机-打脸循环与对抗强度（规则层，并入 creativePlan）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _pick_antagonist_name(character_bible: Optional[dict]) -> str:
    if not isinstance(character_bible, dict):
        return ""
    for key in ("antagonists", "characters"):
        for c in character_bible.get(key) or []:
            if not isinstance(c, dict):
                continue
            rt = str(c.get("roleType") or "")
            if rt.startswith("antagonist") and (c.get("name") or "").strip():
                return (c.get("name") or "").strip()
    return ""


def _major_confrontation_episodes(structure_plan: dict, total_eps: int) -> List[int]:
    eps: set[int] = set()
    for rev in structure_plan.get("keyReversalPoints") or []:
        if not isinstance(rev, dict):
            continue
        ep = rev.get("episodeNumber")
        if ep is not None:
            eps.add(int(ep))
    for milestone in (10, 20, 30, 40, 50, 60, 70, 80):
        if milestone <= total_eps:
            eps.add(milestone)
    return sorted(eps)[:12]


def build_conflict_strategy(
    *,
    structure_plan: Optional[dict] = None,
    character_bible: Optional[dict] = None,
    total_episodes: int = 80,
) -> Dict[str, Any]:
    structure = structure_plan if isinstance(structure_plan, dict) else {}
    total = max(1, int(total_episodes or 80))
    antagonist = _pick_antagonist_name(character_bible)
    major_eps = _major_confrontation_episodes(structure, total)

    cycle: List[dict] = []
    for ep in range(3, total + 1, 3):
        if ep % 10 == 0:
            intensity = "high"
            ctype = "major-confrontation"
        elif ep % 5 == 0:
            intensity = "medium-high"
            ctype = "face-slap"
        else:
            intensity = "medium"
            ctype = "crisis-escalation"
        cycle.append(
            {
                "episode": ep,
                "type": ctype,
                "intensity": intensity,
                "note": f"第{ep}集{'大对抗' if intensity == 'high' else '小危机/打脸循环'}",
            }
        )

    rhythm_notes: List[str] = []
    for block in structure.get("rhythmCurve") or []:
        if not isinstance(block, dict):
            continue
        level = block.get("intensityLevel")
        er = (block.get("episodeRange") or "").strip()
        if er and level is not None:
            rhythm_notes.append(f"{er} 强度 {level}/10")

    pressure = (
        f"反派「{antagonist}」持续施压，主角每 3 集遭遇可拍危机，每 10 集正面硬刚。"
        if antagonist
        else "每 3 集小危机、每 10 集大对抗，保持打脸/逆袭节奏。"
    )

    return {
        "crisisSlapCycleEvery": 3,
        "majorConfrontationEpisodes": major_eps,
        "conflictCycle": cycle[:24],
        "antagonistPressure": pressure,
        "rhythmAlignment": rhythm_notes[:6],
        "notes": "对齐 structurePlan 反转点与节奏曲线，供分集大纲冲突升级参考。",
    }


def merge_conflict_into_creative_plan(
    creative_plan: dict,
    *,
    structure_plan: Optional[dict] = None,
    character_bible: Optional[dict] = None,
    total_episodes: int = 80,
) -> dict:
    out = dict(creative_plan or {})
    if out.get("conflictStrategy"):
        return out
    out["conflictStrategy"] = build_conflict_strategy(
        structure_plan=structure_plan,
        character_bible=character_bible,
        total_episodes=total_episodes,
    )
    return out
