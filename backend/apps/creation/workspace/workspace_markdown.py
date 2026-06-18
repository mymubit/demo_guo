# -*- coding: utf-8 -*-
"""工作台可读 Markdown 预览（对应老版 structure-plan.md / series-outline.md）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..artifact_renderer import episode_to_markdown, episode_scripts_to_markdown
from ..artifact_service import get_artifact
from ..display.character_display import build_character_bible_view
from ..models import Project
from ..outline_skeleton import build_six_stage_blocks
from ..workspace.artifact_keys import artifact_key_for_node
from ..display.structure_display import build_structure_plan_view, normalize_structure_payload


def _lines(*parts: str) -> str:
    return "\n".join(p for p in parts if p).strip()


def _brief_markdown(payload: dict, project: Project) -> str:
    ta = payload.get("targetAudience") or {}
    audience = ""
    if isinstance(ta, dict):
        audience = (ta.get("description") or "").strip()
        age = (ta.get("ageRange") or "").strip()
        if age and audience:
            audience = f"{age} · {audience}"
        elif age:
            audience = age
    elif isinstance(ta, str):
        audience = ta.strip()

    tf = payload.get("trendFormula") or {}
    wb = payload.get("writingBrief") or {}
    parts = [
        "# 立项简报",
        f"**题材**：{payload.get('themeDisplayName') or payload.get('theme') or project.theme}",
        f"**集数**：{payload.get('episodeCount') or project.episode_count}",
        f"**单集时长**：{payload.get('episodeDurationMinutes') or '—'} 分钟",
        f"**平台**：{payload.get('targetPlatform') or getattr(project, 'target_platform', '')}",
        f"**格式**：{payload.get('formatVariantDisplayName') or payload.get('formatVariant') or ''}",
        f"**预算**：{payload.get('budgetLevel') or '—'}",
        f"**创作入口**：{payload.get('creationEntry') or project.creation_entry or '—'}",
        "",
        "## 目标受众",
        audience or "—",
        "",
        "## 故事策划",
        (payload.get("coreHook") or payload.get("coreIdea") or project.core_idea or "—"),
    ]
    if isinstance(wb, dict) and (wb.get("tone") or wb.get("notes")):
        parts.extend(["", "## 写作 Brief", (wb.get("tone") or wb.get("notes") or "")])
    if isinstance(tf, dict) and tf:
        parts.extend(["", "## 题材趋势", str(tf.get("themeDisplayName") or tf.get("theme") or "")])
        if tf.get("audienceFit"):
            parts.append(f"**受众**：{tf['audienceFit']}")
        if tf.get("coreConflictFormula"):
            parts.append(f"**冲突公式**：{tf['coreConflictFormula']}")
        for line in tf.get("highlights") or []:
            if isinstance(line, str) and line.strip():
                parts.append(f"- {line.strip()}")
    ref = (payload.get("referenceWork") or project.reference_work or "").strip()
    if ref:
        parts.extend(["", "## 参考作品", ref])
    notes = (payload.get("notes") or "").strip()
    if notes:
        parts.extend(["", "## 备注", notes])
    return _lines(*parts)


def _structure_markdown(payload: dict, project: Project) -> str:
    payload = normalize_structure_payload(dict(payload), project)
    view = build_structure_plan_view(payload, project)
    parts = ["# 结构与世界观", f"**建议剧名**：{view.get('workingTitle') or '—'}", ""]
    wv = view.get("worldview") or {}
    parts.extend(["## 造梦师全景地图", wv.get("settingSummary") or "—", ""])
    rules = wv.get("rootRules") or []
    if rules:
        parts.append("### 根法则与第一铁律")
        for i, r in enumerate(rules):
            prefix = "第一铁律" if i == 0 else f"规则{i + 1}"
            parts.append(f"- **{prefix}**：{r}")
        parts.append("")
    nouns = wv.get("coreNouns") or []
    if nouns:
        parts.append("### 核心名词表")
        for noun in nouns:
            if isinstance(noun, dict):
                parts.append(f"- **{noun.get('term')}**：{noun.get('definition')}")
        parts.append("")
    sub_world = wv.get("subWorldConsistency") or []
    if sub_world:
        parts.append("### 设定维度")
        for item in sub_world:
            if isinstance(item, dict):
                parts.append(f"- **{item.get('label') or item.get('key')}**：{item.get('text')}")
        parts.append("")

    wv_log = view.get("worldValidationLog") or {}
    if wv_log and not wv_log.get("passed") and not wv_log.get("skipped"):
        parts.append("### 世界观待修项")
        for issue in wv_log.get("issues") or []:
            parts.append(f"- {issue}")
        parts.append("")

    parts.extend(["", "## 六阶段结构"])
    for stage in view.get("sixStagePlan") or []:
        if not isinstance(stage, dict):
            continue
        parts.append(
            f"### 阶段{stage.get('stageIndex')} {stage.get('stageName')} "
            f"（第{stage.get('episodeRange')}集）\n{stage.get('coreTask') or ''}"
        )

    parts.extend(["", "## 节奏曲线"])
    for block in view.get("rhythmCurve") or []:
        if not isinstance(block, dict):
            continue
        events = "；".join(block.get("keyEvents") or [])
        parts.append(
            f"- 第{block.get('episodeRange')}集 · 强度{block.get('intensityLevel')}/10"
            + (f" · {events}" if events else "")
        )

    parts.extend(["", "## 关键反转点"])
    for rev in view.get("keyReversalPoints") or []:
        if isinstance(rev, dict):
            parts.append(f"- 第{rev.get('episodeNumber')}集：{rev.get('description')}")

    arc = view.get("coreStoryArc") or {}
    if any(arc.values()):
        parts.extend(["", "## 核心故事弧"])
        for key, label in (
            ("openingSetup", "开篇"),
            ("escalation", "升级"),
            ("midpointTwist", "中段反转"),
            ("finalConfrontation", "终局对决"),
            ("resolution", "结局"),
        ):
            if arc.get(key):
                parts.append(f"**{label}**：{arc[key]}")
    return _lines(*parts)


def _character_markdown(payload: dict) -> str:
    from ..display.portal_display import portal_gate_log, portal_sanitize_character_bible_view

    view = portal_sanitize_character_bible_view(build_character_bible_view(payload))
    parts = ["# 人物圣经", view.get("summary") or "", ""]
    gate = portal_gate_log(payload.get("characterGateLog") or {})
    if gate and not gate.get("passed") and not gate.get("skipped"):
        parts.extend(["**人设校验**：待补全", ""])
        for issue in (gate.get("issues") or [])[:5]:
            parts.append(f"- {issue}")
        parts.append("")

    for char in view.get("characters") or []:
        parts.append(f"## {char.get('name')}（{char.get('roleTypeLabel') or char.get('roleType')}）")
        if char.get("oneLineSummary"):
            parts.append(char["oneLineSummary"])
        for key, label in (
            ("background", "背景"),
            ("coreMotivation", "核心动机"),
            ("secret", "隐藏秘密"),
        ):
            if char.get(key):
                parts.append(f"\n**{label}**：{char[key]}")
        parts.append("")

    rel_sum = view.get("relationshipSummary")
    if rel_sum:
        parts.extend(["## 人物关系", rel_sum, ""])
    for rel in view.get("relationships") or []:
        parts.append(
            f"- {rel.get('characterAName')} ↔ {rel.get('characterBName')} "
            f"（{rel.get('relationTypeLabel')}）：{rel.get('description')}"
        )
    return _lines(*parts)


def _outline_markdown(payload: dict, project: Project) -> str:
    structure = get_artifact(project, "structure_plan") or {}
    total = int(payload.get("totalEpisodes") or project.episode_count or 80)
    blocks = payload.get("stageBlocks") or build_six_stage_blocks(
        total, structure.get("sixStagePlan")
    )
    parts = ["# 分集大纲与创作规划", f"**总集数**：{total}", ""]

    cp = payload.get("creativePlan") or {}
    if cp:
        parts.append("## 创作规划")
        psych = cp.get("psychologyStrategy") or {}
        if psych:
            archetype = psych.get("dominantArchetype") or ""
            if archetype:
                parts.append(f"- 主需求类型：{archetype}")
            if psych.get("notes"):
                parts.append(f"- 策略说明：{psych['notes']}")
        hd = cp.get("hookDiversity") or {}
        if hd:
            parts.append(f"- 钩子轮换：同类连出上限 {hd.get('maxSameTypeInRow', '—')}")
            req = hd.get("requiredTypes") or []
            if req:
                parts.append(f"- 必选钩子类型：{'、'.join(str(t) for t in req)}")
        for pt in cp.get("paymentCheckpoints") or []:
            if isinstance(pt, dict):
                parts.append(f"- 付费卡点 第{pt.get('episode')}集：{pt.get('description') or pt.get('marker')}")
        for rev in cp.get("reversalSchedule") or []:
            if isinstance(rev, dict):
                line = f"第{rev.get('episode')}集"
                if rev.get("revCode"):
                    line += f" · {rev['revCode']}"
                if rev.get("intensity"):
                    line += f" · {rev['intensity']}"
                if rev.get("setupEpisode"):
                    line += f" · 铺垫第{rev['setupEpisode']}集"
                note = rev.get("note") or rev.get("description") or ""
                parts.append(f"- 反转排期 {line}：{note}" if note else f"- 反转排期 {line}")
        parts.append("")

    summary = (payload.get("structureSummary") or "").strip()
    if summary:
        parts.extend(["## 整体结构总结", summary, ""])

    for hl in payload.get("keyHighlights") or []:
        if isinstance(hl, dict):
            parts.append(f"- 亮点 第{hl.get('episode')}集 · {hl.get('title') or hl.get('description')}")

    parts.append("## 六阶段粗纲")
    for block in blocks:
        if not isinstance(block, dict):
            continue
        rough = (block.get("roughOutline") or "").strip()
        if not rough:
            continue
        fr = block.get("fromEpisode") or block.get("from_episode")
        to = block.get("toEpisode") or block.get("to_episode")
        parts.extend([f"### {block.get('label')}（第{fr}-{to}集）", rough, ""])

    parts.append("## 分集梗概")
    for ep in payload.get("episodes") or []:
        if not isinstance(ep, dict):
            continue
        n = ep.get("episodeNumber")
        summary = (ep.get("oneLineSummary") or "").strip()
        if not summary:
            continue
        parts.append(f"### 第{n}集 {ep.get('title') or ''}\n{summary}")
        if ep.get("hook"):
            parts.append(f"- 钩子：{ep['hook']}")
        if ep.get("cliffhanger"):
            parts.append(f"- 悬念：{ep['cliffhanger']}")
    return _lines(*parts)


def _post_script_appendix(project: Project) -> str:
    from ..artifact_service import get_artifact

    parts: List[str] = []
    review = get_artifact(project, "review_report") or {}
    if review:
        parts.append("## 质检报告（ReviewAgent）")
        parts.append(f"**结果**：{'通过' if review.get('passed') else '待优化'}")
        for issue in (review.get("issues") or [])[:8]:
            parts.append(f"- {issue}")
        parts.append("")

    score = get_artifact(project, "script_score_report") or {}
    overall = score.get("overallScore") or getattr(project, "overall_score", None)
    grade = score.get("grade") or getattr(project, "grade", None)
    if overall is not None or grade:
        parts.extend(["## 深度评分（ScoreAgent）", f"**综合分**：{overall or '—'}", f"**等级**：{grade or '—'}", ""])

    return _lines(*parts)


def _script_markdown(payload: dict) -> str:
    from ..display.portal_display import portal_gate_log

    parts = ["# 剧集剧本"]
    quality = portal_gate_log(payload.get("creatorQualityGuardLog") or {})
    if quality and not quality.get("skipped") and not quality.get("passed"):
        parts.append("**剧本语言校验**：待优化")
        for issue in (quality.get("issues") or [])[:3]:
            parts.append(f"- {issue}")
        parts.append("")

    body = episode_scripts_to_markdown(payload)
    if body:
        parts.append(body)
    else:
        for ep in payload.get("episodes") or []:
            md = ep.get("scriptMarkdown") or episode_to_markdown(ep)
            gate = portal_gate_log(ep.get("gateLog") or {})
            header = f"## 第{ep.get('episodeNumber')}集"
            if gate and not gate.get("skipped") and gate.get("passed") is False:
                header += " · 待修"
                parts.extend([header, md or "（暂无正文）", ""])
                for issue in (gate.get("issues") or [])[:3]:
                    parts.append(f"- {issue}")
                parts.append("")
                continue
            parts.extend([header, md or "（暂无正文）", ""])
    return _lines(*parts)


_BUILDERS = {
    1: lambda p, proj: _brief_markdown(p, proj),
    2: lambda p, proj: _structure_markdown(p, proj),
    3: lambda p, proj: _character_markdown(p),
    4: lambda p, proj: _outline_markdown(p, proj),
    5: lambda p, proj: _script_markdown(p),
}


def build_workspace_markdown(project: Project, node_index: int) -> str:
    key = artifact_key_for_node(node_index)
    if not key:
        return ""
    payload = get_artifact(project, key) or {}
    if not payload:
        return ""
    builder = _BUILDERS.get(node_index)
    if not builder:
        return ""
    try:
        body = builder(payload, project)
        if node_index == 5:
            appendix = _post_script_appendix(project)
            if appendix:
                body = _lines(body, "", appendix)
        return body
    except Exception:  # noqa: BLE001
        return ""
