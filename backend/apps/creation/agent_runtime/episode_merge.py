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
    """剧本/润色分集编号（兼容 episode_num / episode / episodeNumber 等）。"""
    return episode_outline_number(ep)


def episode_design_number(item: dict) -> int:
    """叙事方案分集编号（narrative-plan.v1 episode_id）。"""
    if not isinstance(item, dict):
        return 0
    return _parse_episode_num(item.get("episode_id"))


def episode_outline_number(item: dict) -> int:
    """series-outline.v1 分集编号（v3.1 episode_num / legacy episode_id / schema episode）。"""
    if not isinstance(item, dict):
        return 0
    for key in ("episode_num", "episodeNumber", "episode_id", "episodeId", "episode"):
        num = _parse_episode_num(item.get(key))
        if num:
            return num
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


def filter_episode_outlines_by_range(
    outlines: List[Any],
    episode_from: int,
    episode_to: int,
) -> List[dict]:
    lo = min(int(episode_from), int(episode_to))
    hi = max(int(episode_from), int(episode_to))
    kept: List[dict] = []
    for item in outlines or []:
        if not isinstance(item, dict):
            continue
        num = episode_outline_number(item)
        if lo <= num <= hi:
            kept.append(item)
    return kept


def merge_episode_outlines_by_number(
    existing: dict,
    new_outlines: List[dict],
    *,
    list_key: str = "episode_outlines",
    episode_from: Optional[int] = None,
    episode_to: Optional[int] = None,
) -> dict:
    """按集数合并 series-outline.v1 的 episode_outlines（v3.1 / legacy）。"""
    merged = dict(existing or {})
    by_num: Dict[int, dict] = {}
    for item in merged.get(list_key) or []:
        if not isinstance(item, dict):
            continue
        num = episode_outline_number(item)
        if num:
            by_num[num] = dict(item)
    scoped = new_outlines
    if episode_from is not None and episode_to is not None:
        scoped = filter_episode_outlines_by_range(new_outlines, episode_from, episode_to)
    for item in scoped:
        if not isinstance(item, dict):
            continue
        num = episode_outline_number(item)
        if not num:
            continue
        prev = by_num.get(num) or {}
        by_num[num] = {**prev, **item}
    merged[list_key] = sorted(by_num.values(), key=lambda x: episode_outline_number(x))
    if by_num:
        nums = sorted(by_num.keys())
        merged["target_episode_range"] = f"E{nums[0]:03d}-E{nums[-1]:03d}"
    return merged


SERIES_OUTLINE_STRUCTURE_KEYS = frozenset(
    {
        "six_stage_structure",
        "six_stage_narrative",
        "foreshadowing_list",
        "rhythm_dual_track_validation",
        "ev_et_tp",
        "total_episodes",
    }
)


def _collect_outline_items(payload: dict) -> List[dict]:
    by_num: Dict[int, dict] = {}
    for list_key in ("episode_outlines", "episodes"):
        rows = (payload or {}).get(list_key) or []
        if not isinstance(rows, list):
            continue
        for item in rows:
            if not isinstance(item, dict):
                continue
            num = episode_outline_number(item)
            if num:
                by_num[num] = dict(item)
    return [by_num[n] for n in sorted(by_num.keys())]


def normalize_incoming_outline_numbers(
    items: List[dict],
    *,
    episode_from: int | None,
    episode_to: int | None,
) -> List[dict]:
    """
    修正模型在分批任务中仍输出 1-N 集号的问题。
    当本批为 11-20 但条目集号落在 1-10 时，按批次起点偏移。
    """
    if episode_from is None or episode_to is None:
        return list(items or [])
    scoped = [dict(x) for x in (items or []) if isinstance(x, dict)]
    if not scoped:
        return []

    batch_size = max(1, int(episode_to) - int(episode_from) + 1)
    nums = [episode_outline_number(item) for item in scoped]
    nums = [n for n in nums if n]
    if not nums:
        return [
            {**item, "episode_num": int(episode_from) + index}
            for index, item in enumerate(scoped)
            if int(episode_from) + index <= int(episode_to)
        ]

    min_num = min(nums)
    max_num = max(nums)
    in_batch = all(int(episode_from) <= n <= int(episode_to) for n in nums)
    if in_batch:
        return scoped

    # 模型按 1..N 编号，但请求的是后续批次
    looks_like_local_index = max_num <= batch_size and min_num >= 1
    if looks_like_local_index and int(episode_from) > 1:
        offset = int(episode_from) - 1
        normalized: List[dict] = []
        for item in scoped:
            num = episode_outline_number(item)
            shifted = num + offset if num else None
            if shifted is not None and shifted <= int(episode_to):
                normalized.append({**item, "episode_num": shifted})
        return normalized

    return scoped


def normalize_incoming_episode_numbers(
    items: List[dict],
    *,
    parse_num,
    episode_from: int | None,
    episode_to: int | None,
    number_field: str = "episodeNumber",
) -> List[dict]:
    """分批任务集号偏移（剧本 / 叙事方案等通用）。"""
    if episode_from is None or episode_to is None:
        return list(items or [])
    scoped = [dict(x) for x in (items or []) if isinstance(x, dict)]
    if not scoped:
        return []

    batch_size = max(1, int(episode_to) - int(episode_from) + 1)
    nums = [parse_num(item) for item in scoped]
    nums = [n for n in nums if n]
    if not nums:
        return [
            {**item, number_field: int(episode_from) + index}
            for index, item in enumerate(scoped)
            if int(episode_from) + index <= int(episode_to)
        ]

    min_num = min(nums)
    max_num = max(nums)
    in_batch = all(int(episode_from) <= n <= int(episode_to) for n in nums)
    if in_batch:
        return scoped

    looks_like_local_index = max_num <= batch_size and min_num >= 1
    if looks_like_local_index and int(episode_from) > 1:
        offset = int(episode_from) - 1
        normalized: List[dict] = []
        for item in scoped:
            num = parse_num(item)
            shifted = num + offset if num else None
            if shifted is not None and shifted <= int(episode_to):
                normalized.append({**item, number_field: shifted})
        return normalized

    return scoped


def merge_series_outline_artifact(
    existing: dict | None,
    incoming: dict,
    *,
    episode_from: Optional[int] = None,
    episode_to: Optional[int] = None,
) -> dict:
    """series_outline 专用合并：分集增量写入 + 全剧结构字段保留。"""
    merged = dict(existing or {})
    body = dict(incoming or {})
    existing_items = _collect_outline_items(merged)
    incoming_items = normalize_incoming_outline_numbers(
        _collect_outline_items(body),
        episode_from=episode_from,
        episode_to=episode_to,
    )
    is_batch = episode_from is not None and episode_to is not None

    outline_payload = merge_episode_outlines_by_number(
        {"episode_outlines": existing_items},
        incoming_items,
        episode_from=episode_from,
        episode_to=episode_to,
    )
    merged["episode_outlines"] = outline_payload.get("episode_outlines") or []
    merged.pop("episodes", None)

    if body.get("total_episodes") not in (None, "", [], {}):
        merged["total_episodes"] = body["total_episodes"]
    elif merged.get("total_episodes") in (None, "", [], {}):
        nums = [episode_outline_number(item) for item in merged["episode_outlines"]]
        nums = [n for n in nums if n]
        if nums:
            merged["total_episodes"] = max(nums)

    if is_batch:
        for key, value in body.items():
            if key in {"episode_outlines", "episodes", "_meta", "target_episode_range"}:
                continue
            if key in SERIES_OUTLINE_STRUCTURE_KEYS and merged.get(key) not in (None, {}, [], ""):
                continue
            if value in (None, "", [], {}):
                continue
            merged[key] = value
    else:
        for key, value in body.items():
            if key in {"episode_outlines", "episodes", "_meta", "target_episode_range"}:
                continue
            if value in (None, "", [], {}):
                continue
            merged[key] = value

    nums = sorted(
        episode_outline_number(item)
        for item in merged.get("episode_outlines") or []
        if episode_outline_number(item)
    )
    if nums:
        meta = dict(merged.get("_meta") or {})
        meta["generatedEpisodeCount"] = len(nums)
        meta["generatedEpisodeMax"] = nums[-1]
        if is_batch:
            meta["lastBatchRange"] = f"{episode_from}-{episode_to}"
        merged["_meta"] = meta
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
