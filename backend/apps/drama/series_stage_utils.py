# -*- coding: utf-8 -*-
"""series_outline 六阶段结构归一化（键名 / 字段别名 / 数组合并）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

CANONICAL_STAGE_KEYS = ("opening", "warming", "climax", "turning", "sprint", "ending")

STAGE_KEY_ALIASES: Dict[str, str] = {
    "opening": "opening",
    "open": "opening",
    "开篇": "opening",
    "warming": "warming",
    "warming_up": "warming",
    "warm_up": "warming",
    "warmup": "warming",
    "升温": "warming",
    "climax": "climax",
    "高潮": "climax",
    "turning": "turning",
    "turning_point": "turning",
    "turn": "turning",
    "转折": "turning",
    "sprint": "sprint",
    "final_sprint": "sprint",
    "冲刺": "sprint",
    "ending": "ending",
    "end": "ending",
    "结局": "ending",
    "s1": "opening",
    "s2": "warming",
    "s3": "climax",
    "s4": "turning",
    "s5": "sprint",
    "s6": "ending",
}

STAGE_ID_TO_KEY: Dict[str, str] = {
    "S1": "opening",
    "S2": "warming",
    "S3": "climax",
    "S4": "turning",
    "S5": "sprint",
    "S6": "ending",
}


def normalize_stage_key(raw: Any) -> str:
    text = str(raw or "").strip().lower().replace("-", "_")
    if not text:
        return ""
    if text in STAGE_KEY_ALIASES:
        return STAGE_KEY_ALIASES[text]
    upper = str(raw or "").strip().upper()
    if upper in STAGE_ID_TO_KEY:
        return STAGE_ID_TO_KEY[upper]
    return ""


def stage_text_fields(val: dict) -> str:
    for key in (
        "core_direction",
        "core_design",
        "core_task",
        "stage_goal",
        "summary",
        "stage_name",
        "core_design_task",
    ):
        text = str(val.get(key) or "").strip()
        if text:
            return text
    highlights = val.get("key_plot_points") or val.get("highlights")
    if isinstance(highlights, list):
        parts = [str(item).strip() for item in highlights if str(item).strip()]
        if parts:
            return "；".join(parts[:3])
    return ""


def normalize_stage_payload(val: dict | None) -> dict:
    if not isinstance(val, dict):
        return {}
    ep_range = str(
        val.get("episode_range")
        or val.get("episodes_range")
        or val.get("range")
        or ""
    ).strip()
    proportion = val.get("proportion")
    if proportion in (None, "", [], {}):
        proportion = val.get("stage_proportion")
    return {
        "episode_range": ep_range,
        "core_direction": stage_text_fields(val),
        "proportion": proportion,
    }


def stage_has_content(stage: dict | None) -> bool:
    if not isinstance(stage, dict):
        return False
    norm = normalize_stage_payload(stage)
    return bool(str(norm.get("core_direction") or "").strip() or str(norm.get("episode_range") or "").strip())


def stage_has_displayable_content(stage: dict | None) -> bool:
    """与前端展陈一致：需有阶段描述文本，仅有集数区间不算已生成。"""
    if not isinstance(stage, dict):
        return False
    return bool(str(stage_text_fields(stage) or "").strip())


def normalize_six_stage_structure(
    structure: Any = None,
    *,
    narrative: Any = None,
) -> dict:
    """将 six_stage_structure / six_stage_narrative 统一为 canonical 六键字典。"""
    merged: Dict[str, dict] = {}

    if isinstance(structure, dict):
        for key, val in structure.items():
            canon = normalize_stage_key(key)
            if not canon or not isinstance(val, dict):
                continue
            norm = normalize_stage_payload(val)
            prev = merged.get(canon) or {}
            if stage_has_content(prev) and not stage_has_content(norm):
                continue
            merged[canon] = {**prev, **{k: v for k, v in norm.items() if v not in (None, "", [], {})}}

    if isinstance(narrative, list):
        for item in narrative:
            if not isinstance(item, dict):
                continue
            canon = STAGE_ID_TO_KEY.get(str(item.get("stage_id") or "").strip().upper(), "")
            if not canon:
                canon = normalize_stage_key(item.get("stage_name"))
            if not canon:
                continue
            norm = normalize_stage_payload(
                {
                    "episode_range": item.get("episode_range"),
                    "core_direction": item.get("core_task") or item.get("core_design"),
                    "stage_name": item.get("stage_name"),
                    "stage_proportion": item.get("stage_proportion"),
                    "key_plot_points": item.get("key_plot_points"),
                }
            )
            prev = merged.get(canon) or {}
            if stage_has_content(prev) and not stage_has_content(norm):
                continue
            merged[canon] = {**prev, **{k: v for k, v in norm.items() if v not in (None, "", [], {})}}

    return merged


def merge_six_stage_structure(existing: Any, incoming: Any) -> dict:
    base = normalize_six_stage_structure(existing if isinstance(existing, dict) else {})
    delta = normalize_six_stage_structure(incoming if isinstance(incoming, dict) else {})
    merged = dict(base)
    for key, val in delta.items():
        prev = merged.get(key) or {}
        if stage_has_content(prev) and not stage_has_content(val):
            continue
        merged[key] = {**prev, **val}
    return merged


def project_has_outline_structure(payload: dict | None) -> bool:
    """全剧结构（六阶段 / 伏笔等）是否已有可展示的有效内容。"""
    if not isinstance(payload, dict):
        return False
    stages = normalize_six_stage_structure(
        payload.get("six_stage_structure"),
        narrative=payload.get("six_stage_narrative"),
    )
    if any(stage_has_displayable_content(stage) for stage in stages.values()):
        return True
    foreshadow = payload.get("foreshadowing_list")
    if isinstance(foreshadow, list) and any(
        isinstance(item, dict) and str(item.get("content") or "").strip() for item in foreshadow
    ):
        return True
    rhythm = payload.get("rhythm_dual_track_validation")
    if isinstance(rhythm, dict):
        return any(
            val not in (None, "", [], {})
            for val in rhythm.values()
        )
    return False
