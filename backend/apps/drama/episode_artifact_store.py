# -*- coding: utf-8 -*-
"""
多集产物单集存储 SSOT（通用层）。

- 每集一条 DramaEpisodeArtifact
- ProjectFusionArtifact 仅存结构元数据，不存分集数组
- get_artifact / aggregate_* 聚合后对外保持原有 JSON 形态
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple

from django.db import transaction

from apps.creation.agent_runtime.episode_merge import (
    episode_design_number,
    episode_number,
    normalize_incoming_episode_numbers,
)
from apps.creation.artifact_service import get_artifact, get_fusion_meta_payload, save_artifact
from apps.creation.models import Project
from apps.drama.models import DramaEpisodeArtifact

from apps.drama.artifact_mode import (
    ARTIFACT_MODE_EPISODES_ONLY,
    ARTIFACT_MODE_STRUCTURE_ONLY,
    has_meta_structure,
    resolve_artifact_mode,
)

logger = logging.getLogger(__name__)

EpisodeNumParser = Callable[[dict], int]
ContentChecker = Callable[[dict], bool]

DEFAULT_VERSION = 1


@dataclass(frozen=True)
class EpisodeBlobConfig:
    fusion_key: str
    store_key: str
    list_keys: Tuple[str, ...]
    output_list_key: str
    structure_keys: FrozenSet[str]
    parse_episode_num: EpisodeNumParser
    has_content: ContentChecker
    number_field: str = "episodeNumber"
    version: int = DEFAULT_VERSION
    require_episodes_on_batch: bool = True


def _script_has_content(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    for key in ("full_script_text", "script_text", "scriptMarkdown", "content", "body", "script"):
        if str(item.get(key) or "").strip():
            return True
    scenes = item.get("scenes")
    return isinstance(scenes, list) and len(scenes) > 0


def _narrative_design_has_content(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    return bool(str(item.get("narrative_focus") or item.get("narrativeFocus") or "").strip())


def _estimate_word_count(item: dict) -> int:
    for key in ("full_script_text", "script_text", "scriptMarkdown", "content", "body", "script"):
        text = item.get(key)
        if isinstance(text, str) and text.strip():
            return len(text.strip())
    return 0


EPISODE_SCRIPTS_CONFIG = EpisodeBlobConfig(
    fusion_key="episode_scripts",
    store_key=DramaEpisodeArtifact.ArtifactKey.EPISODE_SCRIPT,
    list_keys=("episodes",),
    output_list_key="episodes",
    structure_keys=frozenset({"nodeId", "projectId"}),
    parse_episode_num=episode_number,
    has_content=_script_has_content,
    number_field="episodeNumber",
)

POLISHED_SCRIPT_CONFIG = EpisodeBlobConfig(
    fusion_key="polished_script",
    store_key=DramaEpisodeArtifact.ArtifactKey.POLISH_RESULT,
    list_keys=("episodes",),
    output_list_key="episodes",
    structure_keys=frozenset({"nodeId", "projectId"}),
    parse_episode_num=episode_number,
    has_content=_script_has_content,
    number_field="episodeNumber",
)

NARRATIVE_PLAN_CONFIG = EpisodeBlobConfig(
    fusion_key="narrative_plan",
    store_key="episode_narrative",
    list_keys=("episode_narrative_designs",),
    output_list_key="episode_narrative_designs",
    structure_keys=frozenset(
        {
            "narrative_core_objective",
            "narrative_mechanics",
            "narrative_consistency_check",
            "opening_package_verification",
        }
    ),
    parse_episode_num=episode_design_number,
    has_content=_narrative_design_has_content,
    number_field="episode_id",
)

EPISODE_BLOB_CONFIGS: Dict[str, EpisodeBlobConfig] = {
    cfg.fusion_key: cfg
    for cfg in (
        EPISODE_SCRIPTS_CONFIG,
        POLISHED_SCRIPT_CONFIG,
        NARRATIVE_PLAN_CONFIG,
    )
}


def get_episode_blob_config(fusion_key: str) -> Optional[EpisodeBlobConfig]:
    return EPISODE_BLOB_CONFIGS.get(fusion_key)


def config_supports_structure_mode(config: EpisodeBlobConfig) -> bool:
    return bool(config.structure_keys - frozenset({"nodeId", "projectId"}))


def project_has_blob_structure(payload: dict | None, config: EpisodeBlobConfig) -> bool:
    return has_meta_structure(payload, config.structure_keys)


def resolve_blob_mode(
    run_params: dict | None,
    *,
    episode_from: Optional[int],
    existing_meta: dict,
    config: EpisodeBlobConfig,
) -> str:
    if not config_supports_structure_mode(config):
        return resolve_artifact_mode(
            run_params,
            episode_from=episode_from,
            existing_meta=existing_meta,
            has_structure=lambda _: False,
        )
    return resolve_artifact_mode(
        run_params,
        episode_from=episode_from,
        existing_meta=existing_meta,
        has_structure=lambda meta: project_has_blob_structure(meta, config),
    )


def _collect_items_from_body(body: dict, config: EpisodeBlobConfig) -> List[dict]:
    by_num: Dict[int, dict] = {}
    sources = [body or {}]
    nested = (body or {}).get(config.fusion_key)
    if isinstance(nested, dict):
        sources.append(nested)
    for source in sources:
        for list_key in config.list_keys:
            rows = source.get(list_key) or []
            if not isinstance(rows, list):
                continue
            for item in rows:
                if not isinstance(item, dict):
                    continue
                num = config.parse_episode_num(item)
                if num:
                    by_num[num] = dict(item)
    return [by_num[n] for n in sorted(by_num.keys())]


def _merge_narrative_mechanics(existing: list | None, incoming: list) -> list:
    existing_mech = list(existing or [])
    seen = {
        str(item.get("mechanism_type") or "").strip()
        for item in existing_mech
        if isinstance(item, dict)
    }
    for item in incoming:
        if not isinstance(item, dict):
            continue
        mech_key = str(item.get("mechanism_type") or "").strip()
        if mech_key and mech_key in seen:
            continue
        existing_mech.append(item)
        if mech_key:
            seen.add(mech_key)
    return existing_mech


def _strip_episode_lists(payload: dict | None, config: EpisodeBlobConfig) -> dict:
    if not isinstance(payload, dict):
        return {}
    return {
        key: value
        for key, value in payload.items()
        if key not in config.list_keys
    }


def upsert_episode_row(
    project: Project,
    config: EpisodeBlobConfig,
    episode_number: int,
    content: dict,
    *,
    agent_id: str = "",
    run_id: str = "",
) -> DramaEpisodeArtifact:
    payload = dict(content or {})
    payload[config.number_field] = config.parse_episode_num(payload) or int(episode_number)
    defaults: dict = {
        "content": payload,
        "produced_by_agent": agent_id or "",
        "diff_summary": f"run:{run_id}"[:500] if run_id else "",
    }
    if config.store_key == DramaEpisodeArtifact.ArtifactKey.EPISODE_SCRIPT:
        defaults["word_count"] = _estimate_word_count(payload)
    obj, _ = DramaEpisodeArtifact.objects.update_or_create(
        project=project,
        episode_number=int(episode_number),
        artifact_key=config.store_key,
        version=config.version,
        defaults=defaults,
    )
    return obj


def list_stored_episode_numbers(project: Project, config: EpisodeBlobConfig) -> List[int]:
    rows = (
        DramaEpisodeArtifact.objects.filter(
            project=project,
            artifact_key=config.store_key,
            version=config.version,
        )
        .order_by("episode_number")
        .values_list("episode_number", "content")
    )
    nums: List[int] = []
    for ep_no, content in rows:
        if isinstance(content, dict) and config.has_content(content):
            nums.append(int(ep_no))
    return nums


def backfill_from_legacy(project: Project, config: EpisodeBlobConfig) -> int:
    exists = DramaEpisodeArtifact.objects.filter(
        project=project,
        artifact_key=config.store_key,
    ).exists()
    if exists:
        return 0
    legacy = get_fusion_meta_payload(project, config.fusion_key)
    items = _collect_items_from_body(legacy, config)
    if not items:
        return 0
    agent_id = str((legacy.get("_meta") or {}).get("agentId") or "")
    saved = 0
    with transaction.atomic():
        for item in items:
            num = config.parse_episode_num(item)
            if not num or not config.has_content(item):
                continue
            upsert_episode_row(project, config, num, item, agent_id=agent_id)
            saved += 1
    if saved:
        logger.info(
            "[EpisodeArtifactStore] legacy backfill fusion=%s project=%s episodes=%s",
            config.fusion_key,
            project.id,
            saved,
        )
    return saved


def load_episode_items(project: Project, config: EpisodeBlobConfig) -> List[dict]:
    backfill_from_legacy(project, config)
    rows = DramaEpisodeArtifact.objects.filter(
        project=project,
        artifact_key=config.store_key,
        version=config.version,
    ).order_by("episode_number")
    items: List[dict] = []
    for row in rows:
        content = dict(row.content or {})
        if not config.has_content(content):
            continue
        num = config.parse_episode_num(content) or int(row.episode_number)
        content[config.number_field] = num
        items.append(content)
    return items


def aggregate_episode_blob(project: Project, config: EpisodeBlobConfig) -> dict:
    structural = _strip_episode_lists(get_fusion_meta_payload(project, config.fusion_key), config)
    items = load_episode_items(project, config)
    nums = [config.parse_episode_num(item) for item in items]
    nums = [n for n in nums if n]
    meta = dict(structural.get("_meta") or {})
    meta.update(
        {
            "storageMode": f"{config.store_key}_per_episode",
            "generatedEpisodeCount": len(items),
            "generatedEpisodeMax": max(nums) if nums else 0,
        }
    )
    return {
        **structural,
        config.output_list_key: items,
        "_meta": meta,
    }


def sync_episode_items_to_store(
    project: Project,
    config: EpisodeBlobConfig,
    items: List[dict],
    *,
    agent_id: str = "",
    run_id: str = "",
) -> List[int]:
    saved: List[int] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        num = config.parse_episode_num(item)
        if not num or not config.has_content(item):
            continue
        upsert_episode_row(project, config, num, item, agent_id=agent_id, run_id=run_id)
        saved.append(num)
    return saved


@transaction.atomic
def persist_episode_blob_output(
    project: Project,
    config: EpisodeBlobConfig,
    body: dict,
    *,
    agent_id: str,
    run_id: str,
    episode_from: Optional[int] = None,
    episode_to: Optional[int] = None,
    run_params: dict | None = None,
) -> List[int]:
    backfill_from_legacy(project, config)
    existing_meta = _strip_episode_lists(get_fusion_meta_payload(project, config.fusion_key), config)
    blob_mode = resolve_blob_mode(
        run_params,
        episode_from=episode_from,
        existing_meta=existing_meta,
        config=config,
    )

    saved_nums: List[int] = []
    incoming: List[dict] = []
    if blob_mode != ARTIFACT_MODE_STRUCTURE_ONLY:
        raw_items = _collect_items_from_body(body, config)
        incoming = normalize_incoming_episode_numbers(
            raw_items,
            parse_num=config.parse_episode_num,
            episode_from=episode_from,
            episode_to=episode_to,
            number_field=config.number_field,
        )
        for item in incoming:
            num = config.parse_episode_num(item)
            if not num or not config.has_content(item):
                continue
            upsert_episode_row(project, config, num, item, agent_id=agent_id, run_id=run_id)
            saved_nums.append(num)

    is_batch = episode_from is not None and episode_to is not None
    merged_meta = dict(existing_meta)
    if blob_mode != ARTIFACT_MODE_EPISODES_ONLY:
        for key, value in (body or {}).items():
            if key in config.list_keys or key == "_meta":
                continue
            if value in (None, "", [], {}):
                continue
            if key == "narrative_mechanics" and isinstance(value, list):
                merged_meta[key] = _merge_narrative_mechanics(merged_meta.get(key), value)
                continue
            merged_meta[key] = value

    run_meta = dict(merged_meta.get("_meta") or {})
    run_meta.update(
        {
            "agentId": agent_id,
            "runId": run_id,
            "storageMode": f"{config.store_key}_per_episode",
            "blobMode": blob_mode,
            "lastSavedEpisodes": saved_nums,
        }
    )
    if is_batch and blob_mode != ARTIFACT_MODE_STRUCTURE_ONLY:
        run_meta["lastBatchRange"] = f"{episode_from}-{episode_to}"
    merged_meta["_meta"] = run_meta
    save_artifact(project, config.fusion_key, merged_meta)

    if blob_mode == ARTIFACT_MODE_STRUCTURE_ONLY:
        if config_supports_structure_mode(config) and not project_has_blob_structure(merged_meta, config):
            raise ValueError(
                f"{config.fusion_key} 全剧结构生成失败：未识别 narrative_core_objective / narrative_mechanics 等有效内容"
            )
        return saved_nums

    if config.require_episodes_on_batch and is_batch and not saved_nums:
        if incoming:
            raise ValueError(
                f"{config.fusion_key} 第{episode_from}-{episode_to}批入库失败："
                f"模型返回 {len(incoming)} 条但均不满足内容校验"
            )
        raise ValueError(
            f"{config.fusion_key} 第{episode_from}-{episode_to}批缺少分集数组 "
            f"({', '.join(config.list_keys)})"
        )
    return saved_nums


def summarize_episode_blob_progress(
    project: Project,
    config: EpisodeBlobConfig,
    *,
    batch_size: int = 5,
) -> dict:
    """分集产物进度（与 outline_progress 结构对齐）。"""
    from apps.drama.outline_progress import suggest_next_outline_range

    backfill_from_legacy(project, config)
    nums = list_stored_episode_numbers(project, config)
    generated_set = set(nums)
    expected = int(project.episode_count or 0)
    missing = [n for n in range(1, expected + 1) if n not in generated_set]
    suggested = suggest_next_outline_range(
        expected=expected,
        generated=generated_set,
        batch_size=batch_size,
    )
    meta = get_fusion_meta_payload(project, config.fusion_key)
    has_structure = (
        project_has_blob_structure(meta, config) if config_supports_structure_mode(config) else False
    )
    return {
        "expected": expected,
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
