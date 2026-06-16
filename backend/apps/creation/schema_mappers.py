# -*- coding: utf-8 -*-
"""
Pipeline / 表单数据 → 技能库 Schema 形态（网站适配技能，不改 demo4book）。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

def _catalog():
    from apps.workflow.fusion.ssot_catalog import get_ssot_catalog

    return get_ssot_catalog()


def _theme_display(theme: str) -> str:
    return _catalog().theme_display_name(theme)


def _format_to_variant(fmt: str) -> str:
    return _catalog().format_variant_schema_key(fmt)


def _format_display(fmt: str) -> str:
    return _catalog().format_variant_display(fmt)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_project_brief(
    project,
    *,
    submit_data: Optional[dict] = None,
    trend_formula: Optional[dict] = None,
    writing_brief: Optional[dict] = None,
    status: str = "confirmed",
) -> Dict[str, Any]:
    """节点1 project-brief.schema.json 形态。"""
    data = submit_data or {}
    variant = _format_to_variant(project.format_variant)
    brief = {
        "nodeId": "node-1-input",
        "projectId": str(project.id),
        "createdAt": _now_iso(),
        "workingTitle": project.title or f"{_theme_display(project.theme)}剧本",
        "theme": project.theme,
        "themeDisplayName": _theme_display(project.theme),
        "episodeCount": project.episode_count,
        "episodeDurationMinutes": float(
            getattr(project, "episode_duration_minutes", None) or data.get("episode_duration_minutes", 2)
        ),
        "targetPlatform": getattr(project, "target_platform", None) or data.get("target_platform", "douyin"),
        "targetAudience": {
            "description": project.audience or data.get("audience", ""),
            "ageRange": data.get("audience_age_range", ""),
            "genderPreference": data.get("audience_gender", ""),
            "habits": data.get("audience_habits", ""),
        },
        "coreHook": project.core_idea,
        "referenceWork": project.reference_work or "",
        "budgetLevel": getattr(project, "budget_level", None) or data.get("budget_level", "medium"),
        "formatVariant": variant,
        "formatVariantDisplayName": _format_display(project.format_variant),
        "status": status,
        "creationEntry": getattr(project, "creation_entry", None) or data.get("creation_entry", "from-scratch"),
        "complianceTier": data.get("compliance_tier", "普通微短剧"),
        "globalMarket": getattr(project, "global_market", None) or data.get("global_market", "domestic"),
    }
    if trend_formula:
        brief["trendFormula"] = trend_formula
    if writing_brief:
        brief["writingBrief"] = writing_brief
    if data.get("notes"):
        brief["notes"] = data["notes"]
    outline_text = (data.get("outline_text") or "").strip()
    novel_text = (data.get("novel_text") or "").strip()
    extra_notes = []
    if outline_text:
        extra_notes.append(f"[分集大纲]\n{outline_text}")
    if novel_text:
        extra_notes.append(f"[小说原文节选]\n{novel_text[:8000]}")
    if extra_notes:
        brief["notes"] = "\n\n".join(filter(None, [brief.get("notes"), *extra_notes]))

    entry = brief.get("creationEntry") or "from-scratch"
    ip_rules = (data.get("ip_keep_rules") or "").strip()
    if entry == "ip-sequel" and ip_rules:
        brief["ipLock"] = {
            "mode": data.get("ip_sequel_mode") or "sequel",
            "keepRoster": [],
            "keepRules": [line.strip() for line in ip_rules.splitlines() if line.strip()],
        }
    return enrich_brief_from_form_seed(brief, project, submit_data=data)


def enrich_brief_from_form_seed(
    brief: Dict[str, Any],
    project,
    *,
    submit_data: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    将用户已在创建流程填写的内容映射为 trendFormula / writingBrief。
    二者为 Agent 内部增强字段，不应在工作台要求用户「补填」。
    """
    out = dict(brief)
    data = submit_data or {}
    theme = (out.get("theme") or getattr(project, "theme", None) or "").strip()

    if not out.get("trendFormula") and theme:
        from .trend_formula import build_trend_formula

        out["trendFormula"] = build_trend_formula(
            theme,
            theme_display_name=out.get("themeDisplayName") or _theme_display(theme),
        )
        out["trendFormula"]["source"] = "form-seed"
    elif isinstance(out.get("trendFormula"), dict) and theme:
        from .trend_formula import normalize_trend_formula

        out["trendFormula"] = normalize_trend_formula(
            out["trendFormula"],
            theme=theme,
            theme_display_name=out.get("themeDisplayName") or _theme_display(theme),
        )

    if isinstance(out.get("trendFormula"), dict):
        from .workspace.workspace_editor import _story_brief_from_payload
        from .trend_formula import apply_project_story_to_trend_formula

        story = _story_brief_from_payload(out)
        out["trendFormula"] = apply_project_story_to_trend_formula(
            out["trendFormula"],
            idea=(data.get("idea") or story.get("idea") or "").strip(),
            opening_hooks=(data.get("opening_hooks") or story.get("openingHooks") or "").strip(),
            core_conflict=(data.get("core_conflict") or story.get("coreConflict") or "").strip(),
        )

    wb = out.get("writingBrief")
    has_writing = isinstance(wb, dict) and (
        (wb.get("tone") or "").strip() or (wb.get("notes") or "").strip()
    )
    if not has_writing:
        tone = (data.get("emotional_tone") or "").strip()
        note_lines: List[str] = []
        for key, label in (
            ("idea", "梗概"),
            ("core_conflict", "核心冲突"),
            ("opening_hooks", "前三集钩子"),
        ):
            val = (data.get(key) or "").strip()
            if val:
                note_lines.append(f"{label}：{val}")
        if not tone or not note_lines:
            from .workspace.workspace_editor import _story_brief_from_payload

            story = _story_brief_from_payload(out)
            tone = tone or (story.get("emotionalTone") or "").strip()
            if story.get("idea") and not any(line.startswith("梗概：") for line in note_lines):
                note_lines.insert(0, f"梗概：{story['idea']}")
            if story.get("coreConflict") and not any(line.startswith("核心冲突：") for line in note_lines):
                note_lines.append(f"核心冲突：{story['coreConflict']}")
            if story.get("openingHooks") and not any(line.startswith("前三集钩子：") for line in note_lines):
                note_lines.append(f"前三集钩子：{story['openingHooks']}")
        if tone or note_lines:
            out["writingBrief"] = {
                "tone": tone,
                "notes": "\n".join(note_lines),
                "source": "form-seed",
            }

    if out.get("trendFormula") or out.get("writingBrief"):
        out["seedEnriched"] = True
    return out


def map_structure_plan(engine: dict, project_brief: dict) -> Dict[str, Any]:
    """节点2 — 引擎 structure → structure-plan 骨架。"""
    acts = engine.get("acts", 6)
    return {
        "nodeId": "node-2-structure",
        "projectId": project_brief.get("projectId"),
        "workingTitle": project_brief.get("workingTitle"),
        "totalEpisodes": engine.get("total_episodes") or project_brief.get("episodeCount"),
        "actStructure": {
            "actCount": acts,
            "reversalPoints": engine.get("reversal_points", []),
            "themeCode": engine.get("theme_code", project_brief.get("theme")),
        },
        "worldview": engine.get("worldview") or {
            "settingSummary": engine.get("setting_summary", project_brief.get("themeDisplayName", "")),
            "timePeriod": "当代",
            "locationType": "urban",
            "rootRules": engine.get("root_rules", [])[:5],
            "coreNouns": [],
            "dreamIndicators": engine.get("dream_indicators")
            or {"absoluteSafety": 7, "efficientSatisfaction": 7, "enhancedRealism": 7, "notes": ""},
        },
        "createdAt": _now_iso(),
    }


def map_character_bible(engine: dict, project_brief: dict) -> Dict[str, Any]:
    """节点3 character-bible 骨架。"""
    chars = []
    prot = engine.get("protagonist") or {}
    if prot:
        chars.append(
            {
                "characterId": "protagonist",
                "name": prot.get("name", "主角"),
                "roleType": "protagonist",
                "archetypeCode": prot.get("archetype", "hero"),
                "oneLineSummary": prot.get("summary", prot.get("description", ""))[:200],
            }
        )
    ant = engine.get("antagonist") or {}
    if ant:
        chars.append(
            {
                "characterId": "antagonist",
                "name": ant.get("name", "反派"),
                "roleType": "antagonist",
                "archetypeCode": ant.get("archetype", "villain"),
                "oneLineSummary": ant.get("summary", "")[:200],
            }
        )
    for i, sc in enumerate(engine.get("supporting_characters") or []):
        chars.append(
            {
                "characterId": f"support-{i+1}",
                "name": sc.get("name", f"配角{i+1}"),
                "roleType": "supporting",
                "archetypeCode": sc.get("role", "ally"),
                "oneLineSummary": (sc.get("description") or sc.get("summary") or "")[:200],
            }
        )
    return {
        "nodeId": "node-3-character",
        "projectId": project_brief.get("projectId"),
        "characters": chars,
        "relationshipSummary": engine.get("relationship_summary", ""),
        "characterCount": engine.get("character_count", len(chars)),
        "createdAt": _now_iso(),
    }


def map_series_outline(engine: dict, project_brief: dict) -> Dict[str, Any]:
    """节点4 series-outline + creativePlan 占位。"""
    episodes_out = []
    for ep in engine.get("episodes") or []:
        episodes_out.append(
            {
                "episodeNumber": ep.get("episode", len(episodes_out) + 1),
                "title": ep.get("title", ""),
                "oneLineSummary": ep.get("summary", ep.get("title", "")),
                "hookTypeCode": ep.get("hook_type_code"),
                "reversalCode": ep.get("reversal_code"),
                "paymentMarker": ep.get("payment_marker"),
            }
        )
    return {
        "nodeId": "node-4-outline",
        "projectId": project_brief.get("projectId"),
        "totalEpisodes": engine.get("total_episodes", len(episodes_out)),
        "creativePlan": engine.get("creative_plan")
        or {
            "hookDiversity": {"maxSameTypeInRow": 2, "requiredTypes": []},
            "paymentCheckpoints": [],
            "reversalSchedule": [],
        },
        "episodes": episodes_out,
        "createdAt": _now_iso(),
    }


def map_episode_scripts(engine: dict, project_brief: dict) -> Dict[str, Any]:
    """节点5 episode-scripts + gateLog 占位。"""
    episodes = []
    for ep in engine.get("episodes") or []:
        episodes.append(
            {
                "episodeNumber": ep.get("episode"),
                "title": ep.get("title"),
                "scriptMarkdown": ep.get("full_script_text", ""),
                "wordCount": ep.get("word_count", 0),
                "sceneCount": ep.get("scenes_count", 0),
                "gateLog": ep.get("gate_log"),
            }
        )
    return {
        "nodeId": "node-5-script",
        "projectId": project_brief.get("projectId"),
        "formatVariant": project_brief.get("formatVariant", "variant-b"),
        "episodes": episodes,
        "totalEpisodes": engine.get("total_episodes", len(episodes)),
        "totalWordCount": engine.get("total_words", 0),
        "createdAt": _now_iso(),
    }


def normalize_score_report_for_api(report: dict) -> dict:
    """8 维报告 → 前端友好结构（兼容 bridge 与完整 schema）。"""
    if not report:
        return {}
    dims = report.get("eightDimensionScores") or {}
    items = []
    labels = {
        "hookStrength": "钩子强度",
        "emotionalDensity": "情感密度",
        "reversalQuality": "反转质量",
        "cliffhangerChain": "悬念链条",
        "characterDepth": "人设深度",
        "dialogueQuality": "台词质量",
        "structureFlow": "结构流畅",
        "productionReadiness": "制作可行性",
    }
    for key, label in labels.items():
        block = dims.get(key) or {}
        raw = block.get("rawScore", block.get("raw_score"))
        if raw is None and isinstance(block, (int, float)):
            raw = block
        weight = block.get("weight", 0)
        contrib = block.get("weightedContribution", block.get("weightedScore", 0))
        items.append(
            {
                "key": key,
                "label": label,
                "rawScore": raw,
                "weight": weight,
                "contribution": contrib,
            }
        )
    return {
        "overallScore": report.get("overallScore"),
        "grade": report.get("grade"),
        "gradeDescription": report.get("gradeDescription", ""),
        "dimensions": items,
        "releasePassScore": report.get("releasePassScore"),
        "skillVersion": report.get("scoringModelVersion"),
    }


def map_pipeline_result_to_artifacts(pipeline_result: dict, project) -> Dict[str, dict]:
    """一次性将 pipeline 结果映射为全部主链 artifact。"""
    brief_engine = pipeline_result.get("project_brief") or {}
    submit = {
        "target_platform": getattr(project, "target_platform", "douyin"),
        "budget_level": getattr(project, "budget_level", "medium"),
        "creation_entry": getattr(project, "creation_entry", "from-scratch"),
    }
    brief = build_project_brief(project, submit_data=submit)
    brief["trendFormula"] = brief_engine.get("trend_formula") or brief.get("trendFormula")
    brief["writingBrief"] = brief_engine.get("writing_brief") or brief.get("writingBrief")

    artifacts = {
        "project_brief": brief,
        "structure_plan": map_structure_plan(pipeline_result.get("structure") or {}, brief),
        "character_bible": map_character_bible(pipeline_result.get("characters") or {}, brief),
        "series_outline": map_series_outline(pipeline_result.get("outlines") or {}, brief),
        "episode_scripts": map_episode_scripts(pipeline_result.get("scripts") or {}, brief),
    }
    return artifacts
