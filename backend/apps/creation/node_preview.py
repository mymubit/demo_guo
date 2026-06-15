# -*- coding: utf-8 -*-
"""C 端节点产物预览（HTML 摘要，绑定技能 SSOT 产物，不暴露 Schema JSON）。"""
from __future__ import annotations

from html import escape
from typing import Any, Dict, List

from apps.workflow.services.pipeline_service import WorkflowPipelineService
from apps.creation.artifact_service import get_artifact
from apps.creation.episode_gate import summarize_episode_gates
from apps.creation.models import Project
from apps.creation.step_mode import artifact_key_for_node, artifacts_for_node


def _li(label: str, value: Any) -> str:
    if value is None or value == "":
        return ""
    return f"<li><strong>{escape(label)}</strong>：{escape(str(value))}</li>"


def _ul(items: List[str]) -> str:
    body = "".join(items)
    return f'<ul class="node-preview-list">{body}</ul>' if body else ""


def _char_names(chars: Any, limit: int = 5) -> List[str]:
    if not isinstance(chars, list):
        return []
    names: List[str] = []
    for c in chars[:limit]:
        if isinstance(c, dict):
            name = c.get("name") or c.get("roleName") or c.get("archetype")
            summary = (c.get("oneLineSummary") or c.get("summary") or "").strip()
            if name and summary:
                names.append(f"{name}（{summary[:48]}）")
            elif name:
                names.append(str(name))
        elif c:
            names.append(str(c))
    return names


def _preview_lines_from_payload(node_index: int, artifact_key: str, payload: dict) -> List[str]:
    if not payload:
        return []

    if node_index == 1 or artifact_key == "project_brief":
        ta = payload.get("targetAudience") or {}
        audience_text = ""
        if isinstance(ta, dict):
            audience_text = (ta.get("description") or "").strip()
            age = (ta.get("ageRange") or "").strip()
            if age and audience_text:
                audience_text = f"{age} · {audience_text}"
            elif age:
                audience_text = age
        elif isinstance(ta, str):
            audience_text = ta.strip()

        core = (payload.get("coreHook") or payload.get("coreIdea") or "").strip()
        duration = payload.get("episodeDurationMinutes")
        duration_text = f"{duration} 分钟/集" if duration else ""

        rows = [
            _li("题材", payload.get("themeDisplayName") or payload.get("theme")),
            _li("集数", payload.get("episodeCount")),
            _li("单集时长", duration_text),
            _li("目标平台", payload.get("targetPlatform")),
            _li("输出格式", payload.get("formatVariantDisplayName") or payload.get("formatVariant")),
            _li("目标受众", audience_text[:300]),
            _li("故事策划", core[:600]),
        ]
        ref = (payload.get("referenceWork") or "").strip()
        if ref:
            rows.append(_li("参考作品", ref[:160]))
        wb = payload.get("writingBrief")
        if isinstance(wb, dict) and wb.get("tone") and wb.get("tone") not in core:
            rows.append(_li("补充基调", wb.get("tone")))
        notes = (payload.get("notes") or "").strip()
        if notes and len(notes) <= 200:
            rows.append(_li("备注", notes))
        return [r for r in rows if r]

    if node_index == 2 or artifact_key == "structure_plan":
        rows = []
        title = (payload.get("workingTitle") or "").strip()
        if title:
            rows.append(_li("项目名称", title))
        rows.append(_li("总集数", payload.get("totalEpisodes")))

        from .display.structure_display import (
            structure_act_count,
            structure_reversal_text,
            structure_worldview_summary,
        )

        worldview = payload.get("worldview") or {}
        setting = structure_worldview_summary(worldview, payload)
        if setting:
            rows.append(_li("世界观", setting[:400]))
        if isinstance(worldview, dict):
            period = worldview.get("timePeriod") or worldview.get("era")
            if period:
                rows.append(_li("时代背景", period))

        act_count = structure_act_count(payload, fallback=0)
        if act_count:
            rows.append(_li("幕结构", f"{act_count} 阶段"))

        reversals = structure_reversal_text(payload)
        if reversals:
            rows.append(_li("反转点", reversals[:300]))

        six = payload.get("sixStagePlan") or []
        if isinstance(six, list) and six:
            names = []
            for stage in six[:6]:
                if isinstance(stage, dict):
                    names.append(stage.get("stageName") or stage.get("coreTask"))
            if names:
                rows.append(_li("阶段划分", " · ".join(n for n in names if n)))
        return [r for r in rows if r]

    if node_index == 3 or artifact_key == "character_bible":
        rows = []
        rel = (payload.get("relationshipSummary") or "").strip()
        if rel:
            rows.append(_li("人物关系", rel[:300]))

        chars = payload.get("characters") or []
        if isinstance(chars, list) and chars:
            by_role: Dict[str, List[str]] = {}
            for c in chars:
                if not isinstance(c, dict):
                    continue
                role = c.get("roleType") or c.get("role") or "角色"
                label = {
                    "protagonist": "主角",
                    "antagonist": "对立",
                    "supporting": "配角",
                }.get(str(role), str(role))
                name = c.get("name") or c.get("roleName") or ""
                summary = (c.get("oneLineSummary") or c.get("summary") or "")[:60]
                line = f"{name}：{summary}" if name and summary else name
                if line:
                    by_role.setdefault(label, []).append(line)
            for label, items in by_role.items():
                rows.append(_li(label, "；".join(items[:4])))
        else:
            for label, key in (("主角", "protagonists"), ("对立", "antagonists"), ("配角", "supporting")):
                names = _char_names(payload.get(key) or [])
                if names:
                    rows.append(_li(label, "；".join(names)))

        if payload.get("characterCount"):
            rows.append(_li("角色数", payload.get("characterCount")))
        gate = payload.get("characterGateLog") or {}
        if gate:
            status = "通过" if gate.get("passed") else "待补全"
            rows.append(_li("人设快检", status))
            if not gate.get("passed"):
                for issue in (gate.get("issues") or [])[:3]:
                    rows.append(_li("待处理", str(issue)[:120]))
        return [r for r in rows if r]

    if node_index == 4 or artifact_key == "series_outline":
        eps = payload.get("episodes") or []
        rows = [_li("大纲集数", len(eps) or payload.get("totalEpisodes"))]
        lines = []
        for ep in eps[:8]:
            if isinstance(ep, dict):
                n = ep.get("episodeNumber") or ep.get("episode")
                t = ep.get("title") or ""
                s = ep.get("oneLineSummary") or ep.get("summary") or ""
                text = f"第{n}集 {t}" if n else t
                if s and s != t:
                    text = f"{text} — {s[:40]}"
                lines.append(text[:56])
        if lines:
            rows.append(_li("分集梗概", "；".join(lines)))
            if len(eps) > 8:
                rows.append(_li("更多", f"共 {len(eps)} 集，此处展示前 8 集"))
        return [r for r in rows if r]

    if node_index == 5 or artifact_key == "episode_scripts":
        eps = payload.get("episodes") or []
        rows = [_li("剧本集数", len(eps))]
        gate = summarize_episode_gates(payload) if eps else None
        if gate:
            rows.append(
                _li(
                    "逐集校验",
                    f"通过 {gate.get('passed', 0)}/{gate.get('total', len(eps))}",
                )
            )
            for ep in (gate.get("failedEpisodes") or [])[:3]:
                num = ep.get("episodeNumber")
                issue = (ep.get("issues") or [""])[0]
                if num is not None:
                    rows.append(_li(f"第{num}集质检", str(issue)[:120]))
        quality = payload.get("creatorQualityGuardLog") or {}
        if quality and not quality.get("skipped"):
            rows.append(
                _li(
                    "AI 套话快检",
                    "通过" if quality.get("passed") else "偏多",
                )
            )
            if not quality.get("passed"):
                for issue in (quality.get("issues") or [])[:3]:
                    rows.append(_li("套话提示", str(issue)[:120]))
        sample = []
        for ep in eps[:5]:
            if isinstance(ep, dict):
                n = ep.get("episodeNumber") or ep.get("episode")
                t = ep.get("title") or ""
                scenes = ep.get("sceneCount")
                words = ep.get("wordCount")
                extra = []
                if scenes:
                    extra.append(f"{scenes} 场")
                if words:
                    extra.append(f"{words} 字")
                suffix = f"（{' · '.join(extra)}）" if extra else ""
                sample.append(f"第{n}集 {t}{suffix}"[:52] if n else f"{t}{suffix}"[:52])
        if sample:
            rows.append(_li("已生成", "；".join(sample)))
            if len(eps) > 5:
                rows.append(_li("更多", f"共 {len(eps)} 集剧本"))
        return [r for r in rows if r]

    return []


def _display_name_for_node(node_index: int, meta: dict, node) -> str:
    name = meta.get("name") or WorkflowPipelineService.display_name_for_index(node_index)
    if node_index == 1 or "信息收集" in name:
        return "立项整理"
    return name.replace("节点", "").strip() or name


def build_node_preview(project: Project, node_index: int) -> Dict[str, Any]:
    meta = WorkflowPipelineService.node_meta_by_index().get(node_index, {})
    node = project.nodes.filter(node_index=node_index).first()
    name = _display_name_for_node(node_index, meta, node)
    artifact_keys = artifacts_for_node(node_index)
    primary_key = artifact_key_for_node(node_index)

    lines: list[str] = [f"<h3>{escape(name)}</h3>"]

    if node_index == 1:
        lines.append(
            '<p class="node-preview-meta">'
            "以下为你前两步已填写内容的整理摘要，将交给后续节点使用。"
            "</p>"
        )

    preview_items: List[str] = []
    for key in artifact_keys:
        payload = get_artifact(project, key)
        if not payload:
            continue
        if node_index == 1 and isinstance(payload, dict):
            payload = dict(payload)
            if not (payload.get("coreHook") or payload.get("coreIdea")) and project.core_idea:
                payload["coreHook"] = project.core_idea
            ta = payload.get("targetAudience")
            if isinstance(ta, dict) and not ta.get("description") and project.audience:
                ta = {**ta, "description": project.audience}
                payload["targetAudience"] = ta
        preview_items.extend(_preview_lines_from_payload(node_index, key, payload))

    if preview_items:
        lines.append(_ul(preview_items))
    elif primary_key:
        lines.append(f'<p class="text-muted">产物尚未生成，请稍候…</p>')

    summary = (node.summary_text if node else "") or ""
    if summary and node_index != 1:
        lines.append(f'<p class="node-preview-summary">{escape(summary)}</p>')

    return {
        "node_index": node_index,
        "display_name": name,
        "fusion_node_id": meta.get("fusion_node_id") or (node.fusion_node_id if node else ""),
        "output_key": meta.get("output_key") or "",
        "sub_skill": meta.get("sub_skill") or "",
        "artifact_key": primary_key or "",
        "artifact_keys": artifact_keys,
        "preview_html": "".join(lines),
        "summary": summary,
    }


def build_completed_node_previews(project: Project) -> List[Dict[str, Any]]:
    """已完成节点的产物预览列表（供进度页展示）。"""
    from .models import CreationNode

    previews: List[Dict[str, Any]] = []
    for n in project.nodes.filter(status=CreationNode.STATUS_COMPLETED).order_by("node_index"):
        try:
            previews.append(build_node_preview(project, n.node_index))
        except Exception:  # noqa: BLE001
            continue
    return previews


def _safe_insight_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    if not report:
        return {}
    structure = report.get("structure") or {}
    analysis = report.get("analysis") or {}
    return {
        "lineCount": structure.get("lineCount"),
        "episodeHeadings": len(structure.get("episodeHeadings") or []),
        "rhythmNotes": (analysis.get("rhythmNotes") or "")[:500],
        "hookPoints": (analysis.get("hookPoints") or [])[:5],
        "cpLines": (analysis.get("cpLines") or [])[:5],
        "compareWithProject": report.get("compareWithProject"),
        "executionTrace": [],
    }


def _safe_polish_summary(polish: Dict[str, Any]) -> Dict[str, Any]:
    if not polish:
        return {}
    suggestions = []
    for i, raw in enumerate((polish.get("suggestions") or [])[:12]):
        if isinstance(raw, dict):
            suggestions.append(
                {
                    "index": i,
                    "episodeNumber": raw.get("episodeNumber") or raw.get("episode"),
                    "field": raw.get("field") or raw.get("action"),
                    "advice": (raw.get("advice") or raw.get("text") or "")[:500],
                    "type": raw.get("type"),
                }
            )
        else:
            suggestions.append({"index": i, "advice": str(raw)[:500]})
    return {
        "suggestionCount": len(polish.get("suggestions") or []),
        "applied": polish.get("applied"),
        "mode": polish.get("mode"),
        "appliedIndices": polish.get("appliedIndices") or [],
        "suggestions": suggestions,
        "executionTrace": [],
    }


def _safe_marketing_summary(kit: Dict[str, Any]) -> Dict[str, Any]:
    if not kit:
        return {}
    return {
        "titles": (kit.get("titles") or [])[:5],
        "clipHooks": (kit.get("clipHooks") or [])[:5],
        "posterSlogans": (kit.get("posterSlogans") or [])[:5],
        "grade": kit.get("grade"),
        "source": kit.get("source"),
        "executionTrace": [],
    }


def build_portal_fusion_snapshot(project: Project) -> Dict[str, Any]:
    """C 端作品详情：节点摘要 + 质检/评分/Agent 产物摘要。"""
    from .artifact_service import build_fusion_snapshot, get_artifact

    meta_by_index = WorkflowPipelineService.node_meta_by_index()
    nodes = []
    for n in project.nodes.all().order_by("node_index"):
        meta = meta_by_index.get(n.node_index, {})
        if meta.get("fusion_node_id") in WorkflowPipelineService.portal_hidden_fusion_node_ids():
            continue
        nodes.append(
            {
                "index": n.node_index,
                "name": n.node_name
                or meta.get("name")
                or WorkflowPipelineService.display_name_for_index(n.node_index),
                "status": n.status,
                "summary": n.summary_text or "",
                "fusion_node_id": n.fusion_node_id or meta.get("fusion_node_id"),
                "output_key": meta.get("output_key") or "",
                "description": meta.get("description") or "",
            }
        )

    snapshot: Dict[str, Any] = {
        "projectId": str(project.id),
        "fusionStatus": project.fusion_status or "",
        "overallScore": project.overall_score,
        "grade": project.grade or "",
        "readyAt": project.ready_at.isoformat() if project.ready_at else None,
        "skillVersion": project.skill_version or "",
        "nodes": nodes,
        "gateSummary": None,
        "scoreReport": None,
        "qualityReport": None,
        "artifactKeys": [],
        "agentArtifacts": {},
    }

    try:
        rich = build_fusion_snapshot(project)
        snapshot["gateSummary"] = rich.get("gateSummary")
        snapshot["scoreReport"] = rich.get("scoreReport")
        snapshot["qualityReport"] = rich.get("qualityReport")
        snapshot["artifactKeys"] = rich.get("artifactKeys") or []
    except Exception:  # noqa: BLE001
        pass

    insight = get_artifact(project, "insight_report") or {}
    marketing = get_artifact(project, "marketing_kit") or {}
    review = get_artifact(project, "review_report") or {}
    polish = get_artifact(project, "polish_log") or {}

    from .monitoring.execution_run_service import AgentExecutionRunService
    from .display.portal_display import portal_strip_agent_block

    def _duration_ms(agent_id: str) -> Optional[int]:
        run = AgentExecutionRunService.latest_run_for_agent(project, agent_id=agent_id)
        if not isinstance(run, dict):
            return None
        return run.get("duration_ms")

    insight_summary = portal_strip_agent_block(_safe_insight_summary(insight)) or {}
    if _duration_ms("insight") is not None:
        insight_summary["durationMs"] = _duration_ms("insight")
    polish_summary = portal_strip_agent_block(_safe_polish_summary(polish)) or {}
    if _duration_ms("polish") is not None:
        polish_summary["durationMs"] = _duration_ms("polish")
    marketing_summary = portal_strip_agent_block(_safe_marketing_summary(marketing)) or {}
    if _duration_ms("marketing") is not None:
        marketing_summary["durationMs"] = _duration_ms("marketing")

    snapshot["agentArtifacts"] = {
        "insight": insight_summary,
        "marketing": marketing_summary,
        "review": portal_strip_agent_block(
            {
                "passed": review.get("passed"),
                "issues": (review.get("issues") or [])[:5],
                "pacingPassed": (review.get("pacing") or {}).get("passed"),
                "durationMs": _duration_ms("review"),
            }
        ),
        "polish": polish_summary,
        "score": portal_strip_agent_block(
            {
                "overallScore": project.overall_score,
                "grade": project.grade or "",
                "durationMs": _duration_ms("score"),
            }
        ),
    }
    return snapshot
