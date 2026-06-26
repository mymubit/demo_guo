# -*- coding: utf-8 -*-
"""Drama 执行产物展示 — 读取项目级 SSOT 产物。"""
from __future__ import annotations

from typing import Any, Dict

from apps.creation.artifact_service import get_artifact
from apps.creation.models import Project
from apps.drama.models import DramaRoleExecution

LIVE_ARTIFACT_KEYS = frozenset(
    {
        "episode_scripts",
        "narrative_plan",
        "polished_script",
    }
)


def resolve_live_output_artifacts(
    drama_exec: DramaRoleExecution,
    *,
    project: Project | None = None,
) -> Dict[str, Any]:
    """合并 execution 快照与项目当前落盘产物。"""
    artifacts = dict(drama_exec.output_artifacts or {})
    proj = project or getattr(drama_exec, "project", None)
    if not proj:
        return artifacts

    # 分集大纲：单集表聚合为 series_outline（SSOT）
    if drama_exec.agent_id == "drama.series-architect" or "series_outline" in artifacts:
        from apps.drama.episode_outline_store import aggregate_series_outline

        aggregated = aggregate_series_outline(proj)
        if aggregated.get("episode_outlines") or aggregated.get("six_stage_structure"):
            artifacts["series_outline"] = aggregated

    for key in LIVE_ARTIFACT_KEYS:
        config = None
        try:
            from apps.drama.episode_artifact_store import EPISODE_BLOB_CONFIGS, aggregate_episode_blob

            config = EPISODE_BLOB_CONFIGS.get(key)
        except Exception:  # noqa: BLE001
            config = None
        if config:
            aggregated = aggregate_episode_blob(proj, config)
            if aggregated.get(config.output_list_key):
                artifacts[key] = aggregated
            continue
        live = get_artifact(proj, key)
        if isinstance(live, dict) and live:
            artifacts[key] = live
    return artifacts
