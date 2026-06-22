# -*- coding: utf-8 -*-
"""ProjectChunk 读写与列表。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.db.models import Max

from apps.creation.models import AgentExecutionRun, Project, ProjectChunk


def resolve_chunk_kind(agent_id: str, artifact_key: str = "") -> str:
    """Agent / 产物键 → chunk kind。"""
    key = (artifact_key or "").strip()
    if key:
        return key
    mapping = {
        "script": "episode_scripts",
        "outline": "series_outline",
        "polish": "episode_scripts",
    }
    return mapping.get((agent_id or "").strip(), "episode_scripts")


def last_chunk_index(project: Project, kind: str) -> Optional[int]:
    result = ProjectChunk.objects.filter(project=project, kind=kind).aggregate(m=Max("index"))
    value = result.get("m")
    return int(value) if value is not None else None


def list_chunks(
    project: Project,
    *,
    kind: str = "episode_scripts",
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    qs = ProjectChunk.objects.filter(project=project, kind=kind).order_by("index")
    total = qs.count()
    rows = qs[offset : offset + limit]
    last_idx = last_chunk_index(project, kind)
    return {
        "items": [{"index": row.index, "data": row.data} for row in rows],
        "total": total,
        "has_more": offset + limit < total,
        "last_episode_index": last_idx,
    }


def upsert_chunk(
    project: Project,
    *,
    kind: str,
    index: int,
    data: Dict[str, Any],
    run: Optional[AgentExecutionRun] = None,
) -> ProjectChunk:
    row, _ = ProjectChunk.objects.update_or_create(
        project=project,
        kind=kind,
        index=index,
        defaults={"data": data, "run": run},
    )
    return row


def chunks_to_episodes(project: Project, kind: str) -> List[Dict[str, Any]]:
    return [row.data for row in ProjectChunk.objects.filter(project=project, kind=kind).order_by("index")]
