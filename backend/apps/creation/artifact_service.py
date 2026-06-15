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
    """
    供 review/score 节点读取已落盘产物的专用接口。

    与 get_artifact 的关键区别：
    1. 若 requesting_node_role 为 review/score，强制只读 DB 已落盘产物（artifact_key 完整记录），
       不接受外部传入的实时中间产物，防止自评偏差。
    2. 若产物尚未落盘（create 节点仍在运行），返回 None 并记录 warning，
       调用方应拒绝启动 review 而非读取进行中的数据。

    参数：
      requesting_node_role — 调用方节点角色，传入 CreationNode.node_role 值；
                             review/score 时会触发隔离校验。
    """
    from .models import CreationNode

    isolation_roles = {CreationNode.ROLE_REVIEW, CreationNode.ROLE_SCORE}
    if requesting_node_role in isolation_roles:
        # 只读 DB 落盘产物，若对应的 create 节点仍在运行则拒绝
        create_running = project.nodes.filter(
            node_role=CreationNode.ROLE_CREATE,
            status=CreationNode.STATUS_RUNNING,
        ).exists()
        if create_running:
            import logging
            logging.getLogger(__name__).warning(
                "get_reviewable_artifact: project=%s artifact_key=%s "
                "拒绝读取——create 节点仍在运行，review 节点不得读取实时中间产物",
                project.id,
                artifact_key,
            )
            return None

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
    for n in project.nodes.all().order_by("node_index"):
        nodes.append(
            {
                "index": n.node_index,
                "fusionNodeId": n.fusion_node_id,
                "name": n.node_name,
                "status": n.status,
                "summary": n.summary_text,
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
