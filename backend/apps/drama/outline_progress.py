# -*- coding: utf-8 -*-
"""series_outline 分集进度统计（存储 SSOT 读取）。"""
from __future__ import annotations

from typing import Any, Dict, List, Set

from apps.creation.agent_runtime.episode_merge import episode_outline_number
from apps.creation.artifact_service import get_artifact, get_fusion_meta_payload
from apps.creation.models import Project

DEFAULT_OUTLINE_BATCH_SIZE = 10

SERIES_OUTLINE_EPISODE_KEYS = ("episode_outlines", "episodes")


def _outline_item_has_content(item: dict) -> bool:
    """判断单集大纲是否有可展示/可入库的有效内容（兼容 v3.1 与 output-schemas 字段）。"""
    if not isinstance(item, dict):
        return False
    for text_key in (
        "oneLineSummary",
        "summary",
        "goal_conflict",
        "core_event",
        "title",
        "episode_name",
        "dual_track_rhythm",
        "subtitle",
    ):
        if str(item.get(text_key) or "").strip():
            return True
    for key in (
        "ending_hook",
        "end_hook",
        "four_segment_structure",
        "ev_et_tp",
        "emotion_markers",
        "emotion_nodes",
        "structure",
        "sections",
    ):
        val = item.get(key)
        if val not in (None, "", [], {}):
            return True
    for seg_key in ("opening", "development", "climax", "resolution"):
        val = item.get(seg_key)
        if val not in (None, "", [], {}):
            return True
    return False


def collect_series_outline_episodes(outline: dict | None) -> List[dict]:
    """合并 episode_outlines / episodes 为统一列表（按集号去重，优先 outlines）。"""
    if not isinstance(outline, dict):
        return []
    by_num: Dict[int, dict] = {}
    for list_key in SERIES_OUTLINE_EPISODE_KEYS:
        rows = outline.get(list_key) or []
        if not isinstance(rows, list):
            continue
        for item in rows:
            if not isinstance(item, dict):
                continue
            num = episode_outline_number(item)
            if not num:
                continue
            by_num[num] = dict(item)
    return [by_num[num] for num in sorted(by_num.keys())]


def generated_episode_numbers(outline: dict | None, *, project: Project | None = None) -> List[int]:
    if project is not None:
        from apps.drama.episode_outline_store import list_episode_outline_numbers

        store_nums = list_episode_outline_numbers(project)
        if store_nums:
            return store_nums
    nums: List[int] = []
    for item in collect_series_outline_episodes(outline):
        num = episode_outline_number(item)
        if num and _outline_item_has_content(item):
            nums.append(num)
    return sorted(set(nums))


def suggest_next_outline_range(
    *,
    expected: int,
    generated: Set[int],
    batch_size: int = DEFAULT_OUTLINE_BATCH_SIZE,
) -> str | None:
    if expected <= 0:
        return None
    size = max(1, int(batch_size))
    start = 1
    while start <= expected and start in generated:
        start += 1
    if start > expected:
        return None
    end = min(start + size - 1, expected)
    return f"{start}-{end}"


def summarize_series_outline_progress(
    project: Project,
    outline: dict | None = None,
    *,
    batch_size: int = DEFAULT_OUTLINE_BATCH_SIZE,
) -> Dict[str, Any]:
    payload = outline if outline is not None else (get_artifact(project, "series_outline") or {})
    expected = int(project.episode_count or 0)
    nums = generated_episode_numbers(payload, project=project)
    generated_set = set(nums)
    missing = [n for n in range(1, expected + 1) if n not in generated_set]
    planned_raw = payload.get("total_episodes") if isinstance(payload, dict) else None
    try:
        planned = int(planned_raw) if planned_raw not in (None, "", [], {}) else expected
    except (TypeError, ValueError):
        planned = expected
    planned = max(planned, expected, max(nums) if nums else 0)
    suggested = suggest_next_outline_range(
        expected=expected,
        generated=generated_set,
        batch_size=batch_size,
    )
    meta = get_fusion_meta_payload(project, "series_outline") if outline is None else None
    from apps.drama.series_stage_utils import project_has_outline_structure

    has_structure = project_has_outline_structure(
        outline if isinstance(outline, dict) else meta,
    )
    return {
        "expected": expected,
        "planned": planned,
        "generated": len(nums),
        "generated_episodes": nums,
        "missing_episodes": missing,
        "missing_count": len(missing),
        "completion_rate": round(len(nums) / expected * 100, 1) if expected else 0.0,
        "suggested_range": suggested,
        "batch_size": batch_size,
        "is_complete": expected > 0 and len(missing) == 0,
        "has_structure": has_structure,
    }
