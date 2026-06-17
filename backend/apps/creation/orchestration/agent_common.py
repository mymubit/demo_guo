# -*- coding: utf-8 -*-
"""Agent 编排公共工具。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

from ..artifact_service import get_artifact
from ..models import Project
from ..schema_mappers import build_project_brief
from ..workspace.workspace_content import ensure_brief_seed_enriched


def deep_merge(base: dict, patch: dict) -> dict:
    out = dict(base)
    for key, val in (patch or {}).items():
        if val is None:
            continue
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def fusion_work_dir(project: Project) -> Path:
    root = Path(getattr(settings, "CREATION_FUSION_WORK_DIR", "/tmp/scriptforge_fusion"))
    work_dir = root / str(project.id)
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


def load_project_brief(project: Project) -> dict:
    ensure_brief_seed_enriched(project)
    brief = get_artifact(project, "project_brief")
    if isinstance(brief, dict) and brief:
        return brief
    return build_project_brief(project)


def build_standard_upstream(
    project: Project,
    brief: dict,
    *,
    structure: Optional[dict] = None,
    character_bible: Optional[dict] = None,
    series_outline: Optional[dict] = None,
) -> Dict[str, Any]:
    structure = structure if structure is not None else (get_artifact(project, "structure_plan") or {})
    character_bible = (
        character_bible if character_bible is not None else (get_artifact(project, "character_bible") or {})
    )
    series_outline = (
        series_outline if series_outline is not None else (get_artifact(project, "series_outline") or {})
    )
    return {
        "projectBrief": brief,
        "project_brief": brief,
        "structurePlan": structure,
        "structure_plan": structure,
        "characterBible": character_bible,
        "character_bible": character_bible,
        "seriesOutline": series_outline,
        "series_outline": series_outline,
        "theme": project.theme or brief.get("theme") or "",
        "episodeCount": project.episode_count or brief.get("episodeCount"),
    }


def write_json_artifact(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
    """仅保留指定集数范围内的分集条目。"""
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
