# -*- coding: utf-8 -*-
"""script 节点 psychology-advisor：分集心理/爽点提示（规则层）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _episode_range_list(start: int, end: int) -> List[int]:
    return list(range(max(1, int(start)), max(int(start), int(end)) + 1))


def build_episode_psychology_hints(
    outline: Optional[dict],
    *,
    from_episode: int,
    to_episode: int,
) -> Dict[str, Any]:
    outline = outline if isinstance(outline, dict) else {}
    cp = outline.get("creativePlan") or {}
    psych = cp.get("psychologyStrategy") or {}
    conflict = cp.get("conflictStrategy") or {}

    dominant = psych.get("dominantArchetype") or "efficient-satisfaction"
    rhythm = psych.get("satisfactionRhythm") or conflict.get("notes") or "每3集小波动，每10集大高潮"
    gap = psych.get("informationGapStrategy") or ""
    pain = psych.get("audiencePainPoint") or ""

    conflict_by_ep = {
        int(item.get("episode")): item
        for item in (conflict.get("conflictCycle") or [])
        if isinstance(item, dict) and item.get("episode") is not None
    }
    reversal_by_ep = {
        int(item.get("episode")): item
        for item in (cp.get("reversalSchedule") or [])
        if isinstance(item, dict) and item.get("episode") is not None
    }
    paywall_eps = {
        int(item.get("episode"))
        for item in (cp.get("paymentCheckpoints") or [])
        if isinstance(item, dict) and item.get("episode") is not None
    }

    episodes_out: List[dict] = []
    for ep in _episode_range_list(from_episode, to_episode):
        notes: List[str] = []
        if pain:
            notes.append(f"受众痛点：{pain[:60]}")
        if gap and ep % 5 == 0:
            notes.append(f"信息差：{gap[:60]}")
        if ep in paywall_eps:
            notes.append("付费卡点集：强化悬念与情绪峰值")
        if ep in reversal_by_ep:
            rev = reversal_by_ep[ep]
            notes.append(f"反转：{rev.get('note') or rev.get('typeLabel') or '关键转折'}")
        if ep in conflict_by_ep:
            cc = conflict_by_ep[ep]
            notes.append(cc.get("note") or f"冲突升级·{cc.get('intensity')}")
        elif ep % 3 == 0:
            notes.append("小危机/打脸循环")
        elif ep % 10 == 0:
            notes.append("大对抗/高潮释放")

        episodes_out.append(
            {
                "episode": ep,
                "dominantArchetype": dominant,
                "satisfactionRhythm": rhythm[:120],
                "directives": notes[:4],
            }
        )

    return {
        "dominantArchetype": dominant,
        "audiencePainPoint": pain[:200],
        "informationGapStrategy": gap[:200],
        "episodes": episodes_out,
        "source": "psychology-advisor-script-rule",
    }
