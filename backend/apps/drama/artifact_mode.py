# -*- coding: utf-8 -*-
"""分批产物写入模式：全剧结构 vs 分集内容。"""
from __future__ import annotations

from typing import Any, Callable, FrozenSet, Optional

ARTIFACT_MODE_FULL = "full"
ARTIFACT_MODE_EPISODES_ONLY = "episodes_only"
ARTIFACT_MODE_STRUCTURE_ONLY = "structure_only"

# plot-architect 历史参数名兼容
OUTLINE_MODE_FULL = ARTIFACT_MODE_FULL
OUTLINE_MODE_EPISODES_ONLY = ARTIFACT_MODE_EPISODES_ONLY
OUTLINE_MODE_STRUCTURE_ONLY = ARTIFACT_MODE_STRUCTURE_ONLY

StructureChecker = Callable[[dict | None], bool]

_META_ONLY_STRUCTURE_KEYS = frozenset({"nodeId", "projectId"})


def resolve_artifact_mode(
    run_params: dict | None,
    *,
    param_keys: tuple[str, ...] = ("blob_mode", "outline_mode", "artifact_mode"),
    episode_from: Optional[int],
    existing_meta: dict,
    has_structure: StructureChecker,
) -> str:
    explicit = ""
    for key in param_keys:
        explicit = str((run_params or {}).get(key) or "").strip()
        if explicit:
            break
    if explicit in (
        ARTIFACT_MODE_FULL,
        ARTIFACT_MODE_EPISODES_ONLY,
        ARTIFACT_MODE_STRUCTURE_ONLY,
    ):
        return explicit
    if has_structure(existing_meta):
        return ARTIFACT_MODE_EPISODES_ONLY
    if episode_from is not None and int(episode_from) > 1:
        return ARTIFACT_MODE_EPISODES_ONLY
    return ARTIFACT_MODE_FULL


def has_meta_structure(
    payload: dict | None,
    structure_keys: FrozenSet[str],
    *,
    extra_checker: StructureChecker | None = None,
) -> bool:
    if extra_checker and extra_checker(payload):
        return True
    if not isinstance(payload, dict):
        return False
    meaningful_keys = structure_keys - _META_ONLY_STRUCTURE_KEYS
    if not meaningful_keys:
        return False
    for key in meaningful_keys:
        value = payload.get(key)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return True
    return False
