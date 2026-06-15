# -*- coding: utf-8 -*-
"""ReviewAgent.pacing-keyword-heuristics — 自 script-pacing-optimizer 迁入。"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from apps.agent.runtime import pacing_heuristics_rules


def _split_episode_blocks(markdown: str) -> List[str]:
    text = (markdown or "").replace("\r\n", "\n").strip()
    if not text:
        return []
    parts = re.split(r"(?=^#\s*第\s*\d+\s*集)", text, flags=re.MULTILINE)
    blocks = [p.strip() for p in parts if p.strip()]
    if blocks:
        return blocks
    return [text]


def _count_keywords(text: str, words: List[str]) -> int:
    total = 0
    for word in words:
        total += len(re.findall(re.escape(word), text))
    return total


def _episode_end_hook(ep_text: str, suspense_words: List[str]) -> bool:
    tail = "\n".join(ep_text.splitlines()[-5:])
    if "？" in tail or "?" in tail:
        return True
    return any(w in tail for w in suspense_words)


def analyze_pacing(markdown: str, *, rules: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """对合并剧本文本做关键词启发式节奏分析。"""
    rules = rules if rules is not None else pacing_heuristics_rules()
    groups = rules.get("keyword_groups") or {}
    thresholds = rules.get("thresholds") or {}

    tension_kw = groups.get("tension") or []
    relax_kw = groups.get("relaxation") or []
    cool_kw = groups.get("cool_point") or []
    suspense_kw = groups.get("suspense") or []
    breath_kw = groups.get("breath_scene") or []

    episodes = _split_episode_blocks(markdown)
    ep_rows: List[Dict[str, Any]] = []
    totals = {
        "tension": 0,
        "relaxation": 0,
        "cool_point": 0,
        "suspense": 0,
        "breath_scene": 0,
    }

    for idx, ep in enumerate(episodes):
        tension = _count_keywords(ep, tension_kw)
        relaxation = _count_keywords(ep, relax_kw)
        cool_point = _count_keywords(ep, cool_kw)
        suspense = _count_keywords(ep, suspense_kw)
        has_breath = any(w in ep for w in breath_kw)
        end_hook = _episode_end_hook(ep, suspense_kw)
        emotion_value = 50 + (tension - relaxation) * 2 + cool_point * 3 + suspense * 2
        emotion_value = max(0, min(100, emotion_value))

        totals["tension"] += tension
        totals["relaxation"] += relaxation
        totals["cool_point"] += cool_point
        totals["suspense"] += suspense
        if has_breath:
            totals["breath_scene"] += 1

        ep_rows.append(
            {
                "episode": idx + 1,
                "tensionCount": tension,
                "relaxationCount": relaxation,
                "coolPointCount": cool_point,
                "suspenseCount": suspense,
                "hasBreathScene": has_breath,
                "endHook": end_hook,
                "emotionValue": emotion_value,
            }
        )

    total_eps = max(1, len(episodes))
    assessments: List[str] = []

    cool_freq = totals["cool_point"] / total_eps
    cool_min = float(thresholds.get("cool_point_per_episode_min", 0.5))
    cool_max = float(thresholds.get("cool_point_per_episode_max", 1.5))
    if cool_freq < cool_min:
        assessments.append("爽点密度不足，建议增加打脸/逆袭/解气类情节")
    elif cool_freq > cool_max:
        assessments.append("爽点密度偏高，注意审美疲劳")
    else:
        assessments.append("爽点密度合适")

    ratio = totals["tension"] / (totals["relaxation"] + 1)
    r_min = float(thresholds.get("tension_relax_ratio_min", 0.5))
    r_max = float(thresholds.get("tension_relax_ratio_max", 3.0))
    if ratio > r_max:
        assessments.append("节奏过于紧张，放松场景偏少")
    elif ratio < r_min:
        assessments.append("节奏过于平缓，冲突张力不足")
    else:
        assessments.append("张弛度合适")

    expected_breath = max(1, int(total_eps / 3))
    if totals["breath_scene"] < expected_breath * 0.5:
        assessments.append(f"喘息场景不足（{totals['breath_scene']} 处，建议至少 {expected_breath} 处）")
    else:
        assessments.append("喘息场景充足")

    hook_count = sum(1 for e in ep_rows if e.get("endHook"))
    hook_ratio = hook_count / total_eps
    hook_min = float(thresholds.get("end_hook_min_ratio", 0.8))
    if hook_ratio < hook_min:
        assessments.append(f"结尾钩子不足（{hook_count}/{total_eps} 集）")
    else:
        assessments.append("结尾钩子充足")

    curve = [e["emotionValue"] for e in ep_rows]
    if len(curve) >= 3:
        big_jumps = sum(
            1 for i in range(1, len(curve)) if abs(curve[i] - curve[i - 1]) > 35
        )
        if big_jumps > max(2, total_eps // 5):
            assessments.append("情绪曲线波动过大，建议平滑过渡")
        else:
            assessments.append("情绪曲线较平滑")

    fail_markers = ("爽点密度不足", "过于紧张", "过于平缓", "结尾钩子不足", "波动过大")
    passed = not any(any(m in a for m in fail_markers) for a in assessments)

    return {
        "totalEpisodes": len(episodes),
        "episodes": ep_rows,
        "overallPacing": totals,
        "emotionCurve": curve,
        "assessments": assessments,
        "passed": passed,
        "source": "pacing-keyword-heuristics",
    }
