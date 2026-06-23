# -*- coding: utf-8 -*-
"""分集产物 merge 工具（从 legacy orchestration 迁出）。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

_EPISODE_ID_NUM_RE = re.compile(r"(?:E|EP|e|ep)?(\d+)")


def _parse_episode_num(raw: Any) -> int:
    if raw in (None, "", [], {}):
        return 0
    if isinstance(raw, int):
        return raw if raw > 0 else 0
    text = str(raw).strip()
    match = _EPISODE_ID_NUM_RE.search(text)
    if match:
        return int(match.group(1))
    try:
        num = int(text)
        return num if num > 0 else 0
    except (TypeError, ValueError):
        return 0


def episode_number(ep: dict) -> int:
    if not isinstance(ep, dict):
        return 0
    return _parse_episode_num(ep.get("episodeNumber"))


def episode_design_number(item: dict) -> int:
    """叙事方案分集编号（narrative-plan.v1 episode_id）。"""
    if not isinstance(item, dict):
        return 0
    return _parse_episode_num(item.get("episode_id"))


def filter_episodes_by_range(
    episodes: List[Any],
    episode_from: int,
    episode_to: int,
) -> List[dict]:
    lo = min(int(episode_from), int(episode_to))
    hi = max(int(episode_from), int(episode_to))
    kept: List[dict] = []
    for ep in episodes or []:
        if not isinstance(ep, dict):
            continue
        num = episode_number(ep)
        if lo <= num <= hi:
            kept.append(ep)
    return kept


def merge_episodes_by_number(
    existing: dict,
    new_episodes: List[dict],
    *,
    episode_from: Optional[int] = None,
    episode_to: Optional[int] = None,
) -> dict:
    merged = dict(existing or {})
    by_num: Dict[int, dict] = {}
    for ep in merged.get("episodes") or []:
        if not isinstance(ep, dict):
            continue
        num = episode_number(ep)
        if num:
            by_num[num] = dict(ep)
    scoped = new_episodes
    if episode_from is not None and episode_to is not None:
        scoped = filter_episodes_by_range(new_episodes, episode_from, episode_to)
    for ep in scoped:
        if not isinstance(ep, dict):
            continue
        num = episode_number(ep)
        if not num:
            continue
        prev = by_num.get(num) or {}
        by_num[num] = {**prev, **ep, "episodeNumber": num}
    merged["episodes"] = sorted(by_num.values(), key=lambda x: episode_number(x))
    return merged


def filter_designs_by_range(
    designs: List[Any],
    episode_from: int,
    episode_to: int,
) -> List[dict]:
    lo = min(int(episode_from), int(episode_to))
    hi = max(int(episode_from), int(episode_to))
    kept: List[dict] = []
    for item in designs or []:
        if not isinstance(item, dict):
            continue
        num = episode_design_number(item)
        if lo <= num <= hi:
            kept.append(item)
    return kept


def merge_episode_designs_by_number(
    existing: dict,
    new_designs: List[dict],
    *,
    list_key: str = "episode_narrative_designs",
    episode_from: Optional[int] = None,
    episode_to: Optional[int] = None,
) -> dict:
    """按集数合并 narrative_plan 等分集叙事设计。"""
    merged = dict(existing or {})
    by_num: Dict[int, dict] = {}
    for item in merged.get(list_key) or []:
        if not isinstance(item, dict):
            continue
        num = episode_design_number(item)
        if num:
            by_num[num] = dict(item)
    scoped = new_designs
    if episode_from is not None and episode_to is not None:
        scoped = filter_designs_by_range(new_designs, episode_from, episode_to)
    for item in scoped:
        if not isinstance(item, dict):
            continue
        num = episode_design_number(item)
        if not num:
            continue
        prev = by_num.get(num) or {}
        by_num[num] = {**prev, **item}
    merged[list_key] = sorted(by_num.values(), key=lambda x: episode_design_number(x))
    if by_num:
        nums = sorted(by_num.keys())
        merged["target_episode_range"] = f"E{nums[0]:03d}-E{nums[-1]:03d}"
    return merged
