# -*- coding: utf-8 -*-
"""industry-benchmarks 规则层读取（节奏/反转密度/场景约束）— DB SSOT。"""
from __future__ import annotations

from typing import Any, Dict

from apps.skill.config.portal.reference_libs import ReferenceLibraryService


def load_industry_benchmarks() -> dict:
    return ReferenceLibraryService.get_json("industry-benchmarks.json")


def episode_structure_benchmarks() -> dict:
    raw = load_industry_benchmarks()
    block = raw.get("episodeStructureBenchmarks")
    return block if isinstance(block, dict) else {}


def reversal_cadence() -> Dict[str, str]:
    block = episode_structure_benchmarks().get("reversalDensity") or {}
    return {
        "small": str(block.get("smallReversal") or "每3集1次"),
        "medium": str(block.get("mediumReversal") or "每10集1次"),
        "large": str(block.get("largeReversal") or "全剧2-4次"),
        "note": str(block.get("note") or ""),
    }


def apply_structure_benchmark_hints(payload: dict) -> dict:
    """为 structure_plan 注入行业基准约束（rhythm-calibrator 后处理）。"""
    if not isinstance(payload, dict):
        return payload
    ep_block = episode_structure_benchmarks()
    cadence = reversal_cadence()
    hints: Dict[str, Any] = {
        "source": "industry-benchmarks",
        "reversalCadence": cadence,
        "episodeDuration": (ep_block.get("episodeDuration") or {}).get("verticalScreen", "90-120秒"),
        "sceneCountPerEpisode": (ep_block.get("sceneCountPerEpisode") or {}).get("benchmark", "1-3个场景"),
        "dialogueMaxChars": 40,
    }

    constraints = payload.get("structuralConstraints")
    if not isinstance(constraints, dict):
        constraints = {}
    merged = {**constraints}
    scene_note = (ep_block.get("sceneCountPerEpisode") or {}).get("benchmark", "1-3")
    try:
        max_scenes = int(str(scene_note).split("-")[-1].replace("个场景", "").strip())
    except ValueError:
        max_scenes = 3
    merged.setdefault("maxScenesPerEpisode", max_scenes)
    merged.setdefault("targetEpisodeSeconds", 90)
    merged.setdefault("smallReversalEveryEpisodes", 3)
    merged.setdefault("majorReversalEveryEpisodes", 10)
    merged["industryBenchmarkHints"] = hints
    payload["structuralConstraints"] = merged

    rhythm = payload.get("rhythmCurve")
    if isinstance(rhythm, list):
        for block in rhythm:
            if isinstance(block, dict) and not block.get("benchmarkNote"):
                block["benchmarkNote"] = cadence.get("note", "")[:200]
    return payload
