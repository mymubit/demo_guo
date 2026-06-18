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

    scripts = get_artifact(project, "episode_scripts") or {}
    gate_summary = summarize_episode_gates(scripts) if scripts else None
    episode_summaries = []
    for ep in (scripts.get("episodes") or [])[:20]:
        gl = ep.get("gateLog") or {}
        episode_summaries.append(
            {
                "episodeNumber": ep.get("episodeNumber"),
                "title": ep.get("title"),
                "gatePassed": gl.get("passed"),
                "gateIssues": (gl.get("issues") or [])[:3],
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
                "fusionNodeId": "",
                "name": run.agent_id or "",
                "status": run.status,
                "summary": (run.output_summary or {}).get("summary", "") if isinstance(run.output_summary, dict) else "",
            }
        )

    return {
        "projectId": str(project.id),
        "fusionStatus": project.fusion_status,
        "overallScore": project.overall_score,
        "grade": project.grade,
        "readyAt": project.ready_at.isoformat() if project.ready_at else None,
        "skillVersion": project.skill_version,
        "projectBrief": {
            "workingTitle": brief.get("workingTitle") or project.title,
            "theme": brief.get("theme") or project.theme,
            "episodeCount": brief.get("episodeCount") or project.episode_count,
            "trendFormula": brief.get("trendFormula"),
            "writingBrief": brief.get("writingBrief"),
        },
        "characterCount": chars.get("characterCount"),
        "outlineEpisodes": outline.get("totalEpisodes"),
        "episodeSummaries": episode_summaries,
        "gateSummary": gate_summary,
        "qualityReport": {
            "finalVerdict": quality.get("finalVerdict"),
            "complianceReport": quality.get("complianceReport"),
        },
        "scoreReport": normalize_score_report_for_api(score_raw),
        "nodes": nodes,
        "artifactKeys": list_artifact_keys(project),
    }
