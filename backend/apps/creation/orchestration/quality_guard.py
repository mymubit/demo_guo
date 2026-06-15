# -*- coding: utf-8 -*-
"""quality-guard：全剧质检阶段 AI 痕迹 / 台词占比 / 刚性扣分（规则层）。"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..dialogue_shaper import line_char_count
from .agent_detection import run_creator_quality_guard

# Tier1 quantitative_constraints:
#   dialogue_chars_per_line_normal=40（软门槛，由 LLM 提示词管控）
#   dialogue_chars_per_line_peak=50  （硬检测绝对上限，超过即强制标记）
#   dialogue_proportion_min=28%       （台词占比最低线）
_MAX_DIALOGUE_CHARS = 50   # 绝对禁止上限（>50字任何情况均违规）
_MIN_DIALOGUE_RATIO = 0.28  # tier1 对齐：28%
_SCORE_WARN = 70
_SCORE_FAIL = 55

# 对齐 tier1.ai_tone_forbidden.forbidden_phrases（max_per_episode=1，超出扣分）
# 静态检测为二次兜底，主防线是 LLM 系统提示词注入
_RIGID_PATTERNS = (
    (r"综上所述", 3, "AI腔套话「综上所述」"),
    (r"总体而言", 3, "AI腔套话「总体而言」"),
    (r"不得不说", 2, "AI腔套话「不得不说」"),
    (r"在这个.*的世界里", 2, "AI腔世界观句式"),
    (r"眼神(变得)?复杂", 4, "模板化描写「眼神复杂」"),
    (r"嘴角扬起[一]?抹(微)?笑", 4, "AI腔叙事套话「嘴角扬起一抹笑」"),
    (r"心中涌起[一]?股", 3, "AI腔叙事套话「心中涌起一股」"),
    (r"情不自禁地", 3, "AI腔副词「情不自禁地」"),
    (r"不由自主地", 3, "AI腔副词「不由自主地」"),
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _episode_plain_text(ep: dict) -> str:
    parts: List[str] = []
    for key in ("scriptMarkdown", "full_script_text"):
        val = (ep.get(key) or "").strip()
        if val:
            parts.append(val)
    for sc in ep.get("scenes") or []:
        if not isinstance(sc, dict):
            continue
        for act in sc.get("actions") or []:
            content = act.get("content", act) if isinstance(act, dict) else act
            parts.append(str(content or ""))
        for dlg in sc.get("dialogues") or []:
            if isinstance(dlg, dict):
                parts.append(str(dlg.get("line") or ""))
    return "\n".join(parts)


def _dialogue_ratio(ep: dict) -> float:
    dialogue_chars = 0
    total_chars = 0
    for sc in ep.get("scenes") or []:
        if not isinstance(sc, dict):
            continue
        for act in sc.get("actions") or []:
            text = str(act.get("content", act) if isinstance(act, dict) else act or "")
            c = line_char_count(text)
            total_chars += c
        for dlg in sc.get("dialogues") or []:
            if not isinstance(dlg, dict):
                continue
            c = line_char_count(str(dlg.get("line") or ""))
            dialogue_chars += c
            total_chars += c
    if total_chars <= 0:
        body = _episode_plain_text(ep)
        if not body.strip():
            return 0.0
        # 粗略：含「：」的行视为对白
        lines = [ln for ln in body.splitlines() if "：" in ln or ":" in ln]
        dlg_len = sum(line_char_count(ln) for ln in lines)
        return dlg_len / max(1, line_char_count(body))
    return dialogue_chars / total_chars


def run_quality_guard(
    payload: dict,
    *,
    score_report: Optional[dict] = None,
) -> Dict[str, Any]:
    """Review 阶段质量快检（扩展 creator-quality-guard）。"""
    base = run_creator_quality_guard(payload if isinstance(payload, dict) else {})
    issues: List[str] = list(base.get("issues") or [])
    assessments: List[str] = []
    deductions: List[Dict[str, Any]] = []

    episodes = (payload or {}).get("episodes") or []
    if not episodes:
        return {
            **base,
            "passed": True,
            "skipped": True,
            "reason": "无剧本文本",
            "checkedAt": _now_iso(),
            "source": "quality-guard",
        }

    low_ratio_eps: List[int] = []
    long_line_eps: List[int] = []
    for ep in episodes:
        if not isinstance(ep, dict):
            continue
        num = int(ep.get("episodeNumber") or ep.get("episode") or 0)
        ratio = _dialogue_ratio(ep)
        if num and ratio < _MIN_DIALOGUE_RATIO:
            low_ratio_eps.append(num)
        for sc in ep.get("scenes") or []:
            if not isinstance(sc, dict):
                continue
            for dlg in sc.get("dialogues") or []:
                if not isinstance(dlg, dict):
                    continue
                if line_char_count(str(dlg.get("line") or "")) > _MAX_DIALOGUE_CHARS:
                    if num and num not in long_line_eps:
                        long_line_eps.append(num)

    if low_ratio_eps:
        sample = "、".join(f"E{n}" for n in low_ratio_eps[:5])
        issues.append(f"台词占比偏低（<{int(_MIN_DIALOGUE_RATIO * 100)}%）：{sample}")
        deductions.append({"code": "dialogue-ratio", "points": 5, "detail": sample})
    else:
        assessments.append("台词占比整体达标")

    if long_line_eps:
        sample = "、".join(f"E{n}" for n in long_line_eps[:5])
        issues.append(f"仍存在超长台词（>{_MAX_DIALOGUE_CHARS}字）：{sample}")
        deductions.append({"code": "long-dialogue", "points": 4, "detail": sample})

    merged_text = "\n".join(_episode_plain_text(ep) for ep in episodes if isinstance(ep, dict))
    for pattern, points, label in _RIGID_PATTERNS:
        hits = len(re.findall(pattern, merged_text))
        if hits:
            deductions.append({"code": label, "points": min(points * hits, 12), "detail": f"{hits} 处"})
            if hits >= 2:
                issues.append(f"刚性扣分：{label} ×{hits}")

    predicted_score: Optional[int] = None
    if isinstance(score_report, dict):
        raw = score_report.get("overallScore") or score_report.get("overall_score")
        if raw is not None:
            try:
                predicted_score = int(round(float(raw)))
            except (TypeError, ValueError):
                predicted_score = None
    if predicted_score is not None:
        assessments.append(f"评分预测 {predicted_score} 分")
        if predicted_score < _SCORE_FAIL:
            issues.append(f"预测评分偏低（{predicted_score} < {_SCORE_FAIL}）")
            deductions.append({"code": "low-score", "points": 8, "detail": str(predicted_score)})
        elif predicted_score < _SCORE_WARN:
            assessments.append("评分处于 B 档，建议润色后再投流")

    total_deduction = sum(int(d.get("points") or 0) for d in deductions)
    passed = bool(base.get("passed")) and len(issues) <= 4 and total_deduction < 15

    return {
        "passed": passed,
        "checkedAt": _now_iso(),
        "source": "quality-guard",
        "creatorGuard": base,
        "assessments": assessments[:8],
        "issues": issues[:12],
        "rigidDeductions": deductions[:10],
        "totalDeductionPoints": total_deduction,
        "predictedScore": predicted_score,
    }
