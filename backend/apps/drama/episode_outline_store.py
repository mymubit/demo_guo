# -*- coding: utf-8 -*-
"""
分集大纲单集存储 SSOT。

- 每集一条 DramaEpisodeArtifact（artifact_key=episode_outline）
- ProjectFusionArtifact.series_outline 仅存全剧结构元数据（六阶段、伏笔等），不存分集数组
- 展示 / 进度 / JSON 通过 aggregate_series_outline() 聚合
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from django.db import transaction

from apps.creation.agent_runtime.episode_merge import (
    episode_outline_number,
    normalize_incoming_outline_numbers,
)
from apps.creation.artifact_service import get_fusion_meta_payload, get_artifact, save_artifact
from apps.creation.models import Project
from apps.drama.models import DramaEpisodeArtifact
from apps.drama.outline_progress import (
    SERIES_OUTLINE_EPISODE_KEYS,
    _outline_item_has_content,
    collect_series_outline_episodes,
)
from apps.drama.series_stage_utils import (
    merge_six_stage_structure,
    normalize_six_stage_structure,
    project_has_outline_structure,
)

logger = logging.getLogger(__name__)

EPISODE_OUTLINE_ARTIFACT_KEY = "episode_outline"
EPISODE_OUTLINE_VERSION = 1


def resolve_outline_mode(
    run_params: dict | None,
    *,
    episode_from: Optional[int],
    existing_meta: dict,
) -> str:
    """分集批次默认只写分集；全剧结构仅在首次或 structure_only 时写入。"""
    return resolve_artifact_mode(
        run_params,
        param_keys=("outline_mode", "blob_mode", "artifact_mode"),
        episode_from=episode_from,
        existing_meta=existing_meta,
        has_structure=project_has_outline_structure,
    )

from apps.drama.artifact_mode import (
    ARTIFACT_MODE_EPISODES_ONLY as OUTLINE_MODE_EPISODES_ONLY,
    ARTIFACT_MODE_FULL as OUTLINE_MODE_FULL,
    ARTIFACT_MODE_STRUCTURE_ONLY as OUTLINE_MODE_STRUCTURE_ONLY,
    resolve_artifact_mode,
)


def _collect_items_from_body(body: dict) -> List[dict]:
    sources: List[dict] = [body or {}]
    nested = (body or {}).get("series_outline")
    if isinstance(nested, dict):
        sources.append(nested)
    by_num: Dict[int, dict] = {}
    for source in sources:
        for list_key in SERIES_OUTLINE_EPISODE_KEYS:
            rows = source.get(list_key) or []
            if not isinstance(rows, list):
                continue
            for item in rows:
                if not isinstance(item, dict):
                    continue
                num = episode_outline_number(item)
                if num:
                    by_num[num] = dict(item)
    return [by_num[n] for n in sorted(by_num.keys())]


def _strip_episode_lists(payload: dict | None) -> dict:
    if not isinstance(payload, dict):
        return {}
    return {
        key: value
        for key, value in payload.items()
        if key not in SERIES_OUTLINE_EPISODE_KEYS
    }


def upsert_episode_outline(
    project: Project,
    episode_number: int,
    content: dict,
    *,
    agent_id: str = "",
    run_id: str = "",
) -> DramaEpisodeArtifact:
    payload = dict(content or {})
    payload["episode_num"] = int(episode_number)
    obj, _ = DramaEpisodeArtifact.objects.update_or_create(
        project=project,
        episode_number=int(episode_number),
        artifact_key=EPISODE_OUTLINE_ARTIFACT_KEY,
        version=EPISODE_OUTLINE_VERSION,
        defaults={
            "content": payload,
            "produced_by_agent": agent_id or "",
            "diff_summary": f"run:{run_id}"[:500] if run_id else "",
        },
    )
    return obj


def list_episode_outline_numbers(project: Project) -> List[int]:
    rows = (
        DramaEpisodeArtifact.objects.filter(
            project=project,
            artifact_key=EPISODE_OUTLINE_ARTIFACT_KEY,
            version=EPISODE_OUTLINE_VERSION,
        )
        .order_by("episode_number")
        .values_list("episode_number", "content")
    )
    nums: List[int] = []
    for ep_no, content in rows:
        if isinstance(content, dict) and _outline_item_has_content(content):
            nums.append(int(ep_no))
    return nums


def backfill_episode_outlines_from_legacy(project: Project) -> int:
    """将旧版 series_outline 内嵌分集迁移到单集表（仅当单集表为空时）。"""
    exists = DramaEpisodeArtifact.objects.filter(
        project=project,
        artifact_key=EPISODE_OUTLINE_ARTIFACT_KEY,
    ).exists()
    if exists:
        return 0
    legacy = get_fusion_meta_payload(project, "series_outline")
    items = collect_series_outline_episodes(legacy)
    if not items:
        return 0
    agent_id = str((legacy.get("_meta") or {}).get("agentId") or "drama.plot-architect")
    saved = 0
    with transaction.atomic():
        for item in items:
            num = episode_outline_number(item)
            if not num or not _outline_item_has_content(item):
                continue
            upsert_episode_outline(project, num, item, agent_id=agent_id)
            saved += 1
    if saved:
        logger.info(
            "[EpisodeOutlineStore] legacy backfill project=%s episodes=%s",
            project.id,
            saved,
        )
    return saved


def load_episode_outlines(project: Project) -> List[dict]:
    backfill_episode_outlines_from_legacy(project)
    rows = DramaEpisodeArtifact.objects.filter(
        project=project,
        artifact_key=EPISODE_OUTLINE_ARTIFACT_KEY,
        version=EPISODE_OUTLINE_VERSION,
    ).order_by("episode_number")
    items: List[dict] = []
    for row in rows:
        content = dict(row.content or {})
        if not _outline_item_has_content(content):
            continue
        content["episode_num"] = int(row.episode_number)
        items.append(content)
    return items


def aggregate_series_outline(project: Project) -> dict:
    """聚合单集大纲 + 全剧结构元数据，供展陈与 API 使用。"""
    structural = _strip_episode_lists(get_fusion_meta_payload(project, "series_outline"))
    episode_outlines = load_episode_outlines(project)
    nums = [episode_outline_number(item) for item in episode_outlines]
    nums = [n for n in nums if n]
    meta = dict(structural.get("_meta") or {})
    meta.update(
        {
            "storageMode": "episode_outline_per_episode",
            "generatedEpisodeCount": len(episode_outlines),
            "generatedEpisodeMax": max(nums) if nums else 0,
        }
    )
    total = structural.get("total_episodes") or project.episode_count
    six_stage = normalize_six_stage_structure(
        structural.get("six_stage_structure"),
        narrative=structural.get("six_stage_narrative"),
    )
    if six_stage:
        structural = {**structural, "six_stage_structure": six_stage}
    return {
        **structural,
        "episode_outlines": episode_outlines,
        "total_episodes": total,
        "_meta": meta,
    }


@transaction.atomic
def persist_series_outline_output(
    project: Project,
    body: dict,
    *,
    agent_id: str,
    run_id: str,
    episode_from: Optional[int] = None,
    episode_to: Optional[int] = None,
    run_params: dict | None = None,
) -> List[int]:
    """
    写入分集大纲：逐集 upsert + 更新全剧结构元数据（不含分集数组）。

    outline_mode:
    - full: 分集 + 全剧结构（默认首批 1-N）
    - episodes_only: 仅写分集，忽略 incoming 结构字段
    - structure_only: 仅写全剧结构，不写分集
    """
    backfill_episode_outlines_from_legacy(project)
    existing_meta = _strip_episode_lists(get_fusion_meta_payload(project, "series_outline"))
    outline_mode = resolve_outline_mode(
        run_params,
        episode_from=episode_from,
        existing_meta=existing_meta,
    )
    from apps.drama.artifact_mode import ARTIFACT_MODE_EPISODES_ONLY, ARTIFACT_MODE_STRUCTURE_ONLY

    saved_nums: List[int] = []
    incoming: List[dict] = []
    if outline_mode != ARTIFACT_MODE_STRUCTURE_ONLY:
        incoming = normalize_incoming_outline_numbers(
            _collect_items_from_body(body),
            episode_from=episode_from,
            episode_to=episode_to,
        )
        for item in incoming:
            num = episode_outline_number(item)
            if not num or not _outline_item_has_content(item):
                continue
            upsert_episode_outline(
                project,
                num,
                item,
                agent_id=agent_id,
                run_id=run_id,
            )
            saved_nums.append(num)

    is_batch = episode_from is not None and episode_to is not None
    merged_meta = dict(existing_meta)
    if outline_mode != ARTIFACT_MODE_EPISODES_ONLY:
        for key, value in (body or {}).items():
            if key in SERIES_OUTLINE_EPISODE_KEYS or key == "_meta":
                continue
            if key == "six_stage_structure" and isinstance(value, dict):
                merged_meta["six_stage_structure"] = merge_six_stage_structure(
                    merged_meta.get("six_stage_structure"),
                    value,
                )
                continue
            if key == "six_stage_narrative" and isinstance(value, list):
                from_narrative = normalize_six_stage_structure(narrative=value)
                if from_narrative:
                    merged_meta["six_stage_structure"] = merge_six_stage_structure(
                        merged_meta.get("six_stage_structure"),
                        from_narrative,
                    )
                merged_meta["six_stage_narrative"] = value
                continue
            if value in (None, "", [], {}):
                continue
            merged_meta[key] = value

        normalized_stage = normalize_six_stage_structure(
            merged_meta.get("six_stage_structure"),
            narrative=merged_meta.get("six_stage_narrative"),
        )
        if normalized_stage:
            merged_meta["six_stage_structure"] = normalized_stage

    if body.get("total_episodes") not in (None, "", [], {}):
        merged_meta["total_episodes"] = body["total_episodes"]
    elif merged_meta.get("total_episodes") in (None, "", [], {}):
        merged_meta["total_episodes"] = project.episode_count

    run_meta = dict(merged_meta.get("_meta") or {})
    run_meta.update(
        {
            "agentId": agent_id,
            "runId": run_id,
            "storageMode": "episode_outline_per_episode",
            "outlineMode": outline_mode,
            "lastSavedEpisodes": saved_nums,
        }
    )
    if is_batch and outline_mode != ARTIFACT_MODE_STRUCTURE_ONLY:
        run_meta["lastBatchRange"] = f"{episode_from}-{episode_to}"
    merged_meta["_meta"] = run_meta
    save_artifact(project, "series_outline", merged_meta)

    if outline_mode == ARTIFACT_MODE_STRUCTURE_ONLY:
        if not project_has_outline_structure(merged_meta):
            raise ValueError("全剧结构生成失败：未识别 six_stage_structure / foreshadowing_list 等有效内容")
        return saved_nums

    if is_batch and not saved_nums:
        if incoming:
            raise ValueError(
                f"分集大纲第{episode_from}-{episode_to}批入库失败："
                f"模型返回 {len(incoming)} 条但均不满足内容校验"
            )
        raise ValueError(
            f"分集大纲第{episode_from}-{episode_to}批缺少 episode_outlines/episodes 数组，"
            "请确保 JSON 含本批分集大纲"
        )

    return saved_nums


def generated_episode_numbers_from_store(project: Project) -> Set[int]:
    backfill_episode_outlines_from_legacy(project)
    return set(list_episode_outline_numbers(project))
