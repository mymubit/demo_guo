"""分集剧本 merge 工具（从 legacy orchestration 迁出）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def episode_number(ep: dict) -> int:
    if not isinstance(ep, dict):
        return 0
    try:
        return int(ep.get("episodeNumber") or ep.get("episode") or 0)
    except (TypeError, ValueError):
        return 0


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
