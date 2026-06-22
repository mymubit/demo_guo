# -*- coding: utf-8 -*-
"""融合产物读写 — artifact_key 对齐 schema_registry。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import Project, ProjectFusionArtifact
from .episode_gate import summarize_episode_gates
from .schema_mappers import normalize_score_report_for_api


def save_artifact(project: Project, artifact_key: str, payload: Any, *, version: int = 1) -> ProjectFusionArtifact:
    obj, _ = ProjectFusionArtifact.objects.update_or_create(
        project=project,
        artifact_key=artifact_key,
        defaults={"payload": payload, "version": version},
    )
    return obj


def save_artifacts_batch(project: Project, artifacts: Dict[str, dict]) -> None:
    for key, payload in artifacts.items():
        if payload is not None:
            save_artifact(project, key, payload)


def get_artifact(project: Project, artifact_key: str) -> Optional[dict]:
    row = ProjectFusionArtifact.objects.filter(project=project, artifact_key=artifact_key).first()
    return row.payload if row else None


def get_reviewable_artifact(
    project: Project,
    artifact_key: str,
    *,
    requesting_node_role: str = "",
) -> Optional[dict]:
    """供 review/score 读取已落盘产物；独立 Agent 模式下与 get_artifact 等价。"""
    _ = requesting_node_role
    return get_artifact(project, artifact_key)


def list_artifact_keys(project: Project) -> List[str]:
    return list(
        ProjectFusionArtifact.objects.filter(project=project)
        .values_list("artifact_key", flat=True)
        .order_by("artifact_key")
    )


def build_fusion_snapshot(project: Project) -> Dict[str, Any]:
    """作品详情/创作完成页用的结构化快照（不含原始全剧 markdown 正文）。"""
    score_raw = get_artifact(project, "script_score_report") or {}
    quality = get_artifact(project, "quality_report") or {}
    brief = get_artifact(project, "project_brief") or {}
    outline = get_artifact(project, "series_outline") or {}
    chars = get_artifact(project, "character_bible") or {}
    review_raw = get_artifact(project, "review_report") or {}
    marketing_raw = get_artifact(project, "marketing_kit") or {}
    polish_raw = get_artifact(project, "polish_log") or {}

    scripts = get_artifact(project, "episode_scripts") or {}
    gate_summary = summarize_episode_gates(scripts) if scripts else None
    episode_summaries = []
    for ep in (scripts.get("episodes") or [])[:20]:
        gl = ep.get("gateLog") or ep.get("gate_log") or {}
        episode_summaries.append(
            {
                "episode_number": ep.get("episodeNumber") or ep.get("episode_number"),
                "title": ep.get("title"),
                "gate_passed": gl.get("passed"),
                "gate_issues": (gl.get("issues") or [])[:3],
            }
        )

    nodes = []
    from .models import AgentExecutionRun

    seen_indices: set[int] = set()
    for run in AgentExecutionRun.objects.filter(project=project).order_by("node_index", "-started_at"):
        if run.node_index is None or int(run.node_index) in seen_indices:
            continue
        seen_indices.add(int(run.node_index))
        nodes.append(
            {
                "index": int(run.node_index),
                "fusion_node_id": "",
                "name": run.agent_id or "",
                "status": run.status,
                "summary": (run.output_summary or {}).get("summary", "") if isinstance(run.output_summary, dict) else "",
            }
        )

    from apps.drama.progress_service import DramaProjectProgressService

    drama = DramaProjectProgressService.find_drama_project(project.id)

    return {
        "project_id": str(project.id),
        "current_stage": drama.current_stage if drama else "",
        "current_stage_text": DramaProjectProgressService.drama_stage_label(
            drama.current_stage if drama else ""
        ),
        "delivery_status": (drama.delivery_status if drama else "") or "",
        "track_mode": drama.track_mode if drama else "",
        "overall_score": project.overall_score,
        "grade": project.grade,
        "ready_at": project.ready_at.isoformat() if project.ready_at else None,
        "skill_version": project.skill_version,
        "project_brief": {
            "working_title": brief.get("workingTitle") or brief.get("working_title") or project.title,
            "theme": brief.get("theme") or project.theme,
            "episode_count": brief.get("episodeCount") or brief.get("episode_count") or project.episode_count,
            "trend_formula": brief.get("trendFormula") or brief.get("trend_formula"),
            "writing_brief": brief.get("writingBrief") or brief.get("writing_brief"),
        },
        "character_count": chars.get("characterCount") or chars.get("character_count"),
        "outline_episodes": outline.get("totalEpisodes") or outline.get("total_episodes"),
        "episode_summaries": episode_summaries,
        "gate_summary": gate_summary,
        "quality_report": {
            "final_verdict": quality.get("finalVerdict") or quality.get("final_verdict"),
            "compliance_report": quality.get("complianceReport") or quality.get("compliance_report"),
        },
        "score_report": normalize_score_report_for_api(score_raw),
        "review_report": {
            "passed": review_raw.get("passed"),
            "issues": review_raw.get("issues") or [],
            "pacing_passed": review_raw.get("pacingPassed") or review_raw.get("pacing_passed"),
        }
        if review_raw
        else None,
        "marketing_kit": {
            "titles": marketing_raw.get("titles") or [],
            "clip_hooks": marketing_raw.get("clipHooks") or marketing_raw.get("clip_hooks") or [],
            "poster_slogans": marketing_raw.get("posterSlogans") or marketing_raw.get("poster_slogans") or [],
        }
        if marketing_raw
        else None,
        "polish_log": {
            "suggestions": polish_raw.get("suggestions") or [],
            "applied": polish_raw.get("applied"),
        }
        if polish_raw
        else None,
        "nodes": nodes,
        "artifact_keys": list_artifact_keys(project),
    }
