# -*- coding: utf-8 -*-
"""plot-structure-review：反转/悬念/节奏平台期结构检测（规则层）。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _episode_nums_with_field(episodes: List[dict], field: str) -> set[int]:
    out: set[int] = set()
    for ep in episodes or []:
        if not isinstance(ep, dict):
            continue
        num = ep.get("episodeNumber")
        if num is None:
            continue
        val = ep.get(field)
        if isinstance(val, str) and val.strip():
            out.add(int(num))
        elif val:
            out.add(int(num))
    return out


def _flat_rhythm_segments(rhythm_curve: List[dict], *, max_level: int = 5) -> List[str]:
    flats: List[str] = []
    for block in rhythm_curve or []:
        if not isinstance(block, dict):
            continue
        level = block.get("intensityLevel")
        if level is None:
            continue
        if int(level) <= max_level:
            er = (block.get("episodeRange") or "").strip()
            if er:
                flats.append(er)
    return flats


def analyze_plot_structure(
    *,
    structure_plan: Optional[dict] = None,
    series_outline: Optional[dict] = None,
    episode_scripts: Optional[dict] = None,
) -> Dict[str, Any]:
    structure = structure_plan if isinstance(structure_plan, dict) else {}
    outline = series_outline if isinstance(series_outline, dict) else {}
    scripts = episode_scripts if isinstance(episode_scripts, dict) else {}

    issues: List[str] = []
    assessments: List[str] = []

    rev_points = [
        int(r.get("episodeNumber"))
        for r in (structure.get("keyReversalPoints") or [])
        if isinstance(r, dict) and r.get("episodeNumber") is not None
    ]
    outline_eps = outline.get("episodes") or []
    outline_count = len([e for e in outline_eps if isinstance(e, dict)])
    script_eps = scripts.get("episodes") or []
    script_count = len([e for e in script_eps if isinstance(e, dict)])

    if rev_points:
        assessments.append(f"结构规划含 {len(rev_points)} 个关键反转点")
        if outline_count:
            reversal_eps = _episode_nums_with_field(outline_eps, "reversal")
            reversal_eps |= _episode_nums_with_field(outline_eps, "reversalCode")
            missing = [ep for ep in rev_points if ep not in reversal_eps]
            if missing:
                sample = "、".join(f"E{n}" for n in missing[:5])
                issues.append(f"大纲未标注反转字段：{sample}")
            else:
                assessments.append("大纲与结构反转点基本对齐")
    else:
        issues.append("结构规划缺少 keyReversalPoints")

    if outline_count:
        cliff_eps = _episode_nums_with_field(outline_eps, "cliffhanger")
        cliff_ratio = len(cliff_eps) / max(1, outline_count)
        if cliff_ratio < 0.6:
            issues.append(f"悬念结尾不足（{len(cliff_eps)}/{outline_count} 集有 cliffhanger）")
        else:
            assessments.append(f"悬念结尾覆盖 {len(cliff_eps)}/{outline_count} 集")

        hook_codes = [
            (e.get("hookTypeCode") or "").strip()
            for e in outline_eps
            if isinstance(e, dict) and (e.get("hookTypeCode") or "").strip()
        ]
        if hook_codes:
            unique = len(set(hook_codes))
            assessments.append(f"钩子类型 {unique} 种（已标注 {len(hook_codes)} 集）")
            if unique < 3 and len(hook_codes) >= 5:
                issues.append("钩子类型多样性偏低，建议轮换 hook-types-library")
        elif outline_count >= 3:
            issues.append("前若干集大纲缺少 hookTypeCode 标注")

    flats = _flat_rhythm_segments(structure.get("rhythmCurve") or [])
    if flats:
        assessments.append(f"节奏平台期段：{', '.join(flats[:4])}")
        if len(flats) >= 3:
            issues.append("节奏曲线低强度段偏多，注意中段注水风险")

    if script_count and outline_count:
        if script_count < outline_count * 0.5:
            issues.append(f"剧本完成度偏低（{script_count}/{outline_count} 集）")
        else:
            assessments.append(f"剧本进度 {script_count}/{outline_count} 集")

    fail_markers = ("缺少", "不足", "偏低", "未标注", "注水")
    passed = not any(any(m in i for m in fail_markers) for i in issues)

    return {
        "passed": passed,
        "checkedAt": _now_iso(),
        "reversalPointCount": len(rev_points),
        "outlineEpisodeCount": outline_count,
        "scriptEpisodeCount": script_count,
        "assessments": assessments[:10],
        "issues": issues[:12],
        "source": "plot-structure-review",
    }
