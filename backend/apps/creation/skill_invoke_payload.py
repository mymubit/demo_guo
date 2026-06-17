# -*- coding: utf-8 -*-
"""工作台 SkillInvoker 入参构建与输出落库。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .artifact_service import get_artifact, save_artifact
from .models import Project
from .schema_mappers import build_project_brief, map_character_bible, map_structure_plan
from .step_mode import artifact_key_for_node


def _load_brief(project: Project) -> dict:
    from .workspace.workspace_content import ensure_brief_seed_enriched

    ensure_brief_seed_enriched(project)
    brief = get_artifact(project, "project_brief")
    if isinstance(brief, dict) and brief:
        return brief
    return build_project_brief(project)


def _resolve_episode_count(project: Project, brief: dict) -> int:
    try:
        count = int(getattr(project, "episode_count", None) or brief.get("episodeCount") or 0)
    except (TypeError, ValueError):
        count = 0
    return max(count, 1)


def _characters_for_skill(project: Project) -> List[dict]:
    bible = get_artifact(project, "character_bible") or {}
    chars = bible.get("characters")
    return list(chars) if isinstance(chars, list) else []


def _outlines_for_skill(
    project: Project,
    *,
    episode_from: Optional[int] = None,
    episode_to: Optional[int] = None,
) -> List[dict]:
    outline = get_artifact(project, "series_outline") or {}
    if isinstance(outline.get("outlines"), list):
        episodes = list(outline["outlines"])
    else:
        episodes = []
        for ep in outline.get("episodes") or []:
            if not isinstance(ep, dict):
                continue
            num = int(ep.get("episodeNumber") or ep.get("episode") or 0)
            episodes.append(
                {
                    "episode": num,
                    "title": ep.get("title") or "",
                    "scenes": ep.get("scenes") or [],
                    "key_dialogues": ep.get("keyDialogues") or ep.get("key_dialogues") or [],
                    "hook": ep.get("hook") or ep.get("oneLineSummary") or "",
                    "tension_level": ep.get("tensionLevel") or ep.get("tension_level") or 0.5,
                }
            )
    if episode_from is None and episode_to is None:
        return episodes
    filtered: List[dict] = []
    for item in episodes:
        if not isinstance(item, dict):
            continue
        num = int(item.get("episode") or item.get("episodeNumber") or 0)
        if episode_from is not None and num < episode_from:
            continue
        if episode_to is not None and num > episode_to:
            continue
        filtered.append(item)
    return filtered


def _scripts_for_skill(
    project: Project,
    *,
    episode_from: Optional[int] = None,
    episode_to: Optional[int] = None,
) -> List[dict]:
    scripts = get_artifact(project, "episode_scripts") or {}
    result: List[dict] = []
    for ep in scripts.get("episodes") or []:
        if not isinstance(ep, dict):
            continue
        num = int(ep.get("episodeNumber") or ep.get("episode") or 0)
        if episode_from is not None and num < episode_from:
            continue
        if episode_to is not None and num > episode_to:
            continue
        result.append(
            {
                "episode": num,
                "title": ep.get("title") or "",
                "content": ep.get("scriptMarkdown") or ep.get("content") or "",
            }
        )
    return result


def build_creation_skill_invoke_payload(
    project: Project,
    skill_id: str,
    *,
    script_from: Optional[int] = None,
    script_to: Optional[int] = None,
    outline_mode: Optional[str] = None,
    outline_stage_key: Optional[str] = None,
    skip_skill_quota: bool = True,
) -> dict:
    """从项目产物构建符合 input_schema 的技能调用 payload。"""
    brief = _load_brief(project)
    episode_count = _resolve_episode_count(project, brief)
    payload: Dict[str, Any] = {
        "project_id": str(project.id),
        "skip_skill_quota": skip_skill_quota,
    }
    if script_from is not None:
        payload["script_from"] = script_from
    if script_to is not None:
        payload["script_to"] = script_to
    if outline_mode:
        payload["outline_mode"] = outline_mode
    if outline_stage_key:
        payload["outline_stage_key"] = outline_stage_key

    if skill_id == "creation.brief":
        audience = project.audience or ""
        target = brief.get("targetAudience")
        if isinstance(target, dict) and not audience:
            audience = str(target.get("description") or "")
        payload.update(
            {
                "theme": project.theme or brief.get("theme") or "",
                "core_idea": project.core_idea or brief.get("coreHook") or "",
                "audience": audience,
                "reference_work": project.reference_work or brief.get("referenceWork") or "",
            }
        )
    elif skill_id == "creation.structure":
        payload.update(
            {
                "brief": brief,
                "episode_count": episode_count,
                "target_platform": brief.get("targetPlatform")
                or getattr(project, "target_platform", None)
                or "douyin",
            }
        )
    elif skill_id == "creation.character":
        structure = get_artifact(project, "structure_plan") or {}
        payload.update({"brief": brief, "structure": structure})
    elif skill_id == "creation.outline":
        structure = get_artifact(project, "structure_plan") or {}
        payload.update(
            {
                "brief": brief,
                "structure": structure,
                "characters": _characters_for_skill(project),
            }
        )
        if script_from is not None:
            payload["episode_from"] = script_from
        if script_to is not None:
            payload["episode_to"] = script_to
    elif skill_id == "creation.script":
        outlines = _outlines_for_skill(project, episode_from=script_from, episode_to=script_to)
        if not outlines:
            outlines = _outlines_for_skill(project)
        payload.update(
            {
                "outlines": outlines,
                "characters": _characters_for_skill(project),
            }
        )
        if script_from is not None:
            payload["episode_from"] = script_from
        if script_to is not None:
            payload["episode_to"] = script_to
    elif skill_id == "creation.review":
        payload.update(
            {
                "scripts": _scripts_for_skill(project),
                "brief": brief,
            }
        )
    elif skill_id == "creation.polish":
        review = get_artifact(project, "review_report") or {}
        payload.update(
            {
                "scripts": _scripts_for_skill(project),
                "review": review,
            }
        )

    return payload


def apply_creation_skill_output(
    project: Project,
    node_index: int,
    skill_id: str,
    skill_data: dict,
) -> str:
    """将 SkillInvoker 输出写入 fusion artifact 并标记节点完成。"""
    from django.utils import timezone

    from .display.structure_display import enrich_structure_payload, normalize_structure_payload
    from .workspace.workspace_editor import _mark_skill_has_content

    if not isinstance(skill_data, dict):
        skill_data = {}

    brief = _load_brief(project)
    artifact_key = artifact_key_for_node(node_index) or ""

    if skill_id == "creation.structure":
        engine = {
            "total_episodes": skill_data.get("episode_count") or brief.get("episodeCount"),
            "acts": len(skill_data.get("acts") or []) or 6,
            "reversal_points": [
                {
                    "episode": item.get("episode"),
                    "type": item.get("type"),
                    "description": item.get("description"),
                }
                for item in (skill_data.get("plot_twists") or [])
                if isinstance(item, dict)
            ],
            "worldview": {
                "setting_summary": brief.get("themeDisplayName") or brief.get("theme") or "",
            },
        }
        payload = map_structure_plan(engine, brief)
        acts = skill_data.get("acts") or []
        if isinstance(acts, list) and acts:
            payload["sixStagePlan"] = [
                {
                    "stageIndex": idx + 1,
                    "stageName": act.get("name") or f"阶段{idx + 1}",
                    "startEpisode": 0,
                    "endEpisode": 0,
                    "coreTask": act.get("purpose") or "",
                    "roughOutline": act.get("episodes") or "",
                }
                for idx, act in enumerate(acts)
                if isinstance(act, dict)
            ]
        payload = enrich_structure_payload(
            payload,
            theme=project.theme or "",
            episode_count=payload.get("totalEpisodes"),
        )
        payload = normalize_structure_payload(payload, project)
        save_artifact(project, "structure_plan", payload)
        artifact_key = "structure_plan"
        _mark_skill_has_content(
            project,
            node_index,
            f"{payload.get('totalEpisodes', project.episode_count)}集结构规划",
        )

    elif skill_id == "creation.character":
        raw_chars = skill_data.get("characters") or []
        engine_chars: List[dict] = []
        for idx, ch in enumerate(raw_chars):
            if not isinstance(ch, dict):
                continue
            item = dict(ch)
            if not item.get("roleType"):
                role = str(item.get("role") or "").lower()
                if "主角" in role or role == "protagonist":
                    item["roleType"] = "protagonist"
                elif "反派" in role or "antagonist" in role:
                    item["roleType"] = "antagonist"
                else:
                    item["roleType"] = "supporting"
            item.setdefault("characterId", f"char-{idx + 1}")
            engine_chars.append(item)
        payload = map_character_bible({"characters": engine_chars}, brief)
        save_artifact(project, "character_bible", payload)
        artifact_key = "character_bible"
        count = payload.get("characterCount", len(payload.get("characters") or []))
        _mark_skill_has_content(project, node_index, f"共 {count} 个角色")

    elif skill_id == "creation.outline":
        existing = get_artifact(project, "series_outline") or {}
        merged = dict(existing)
        new_eps: List[dict] = []
        for item in skill_data.get("outlines") or []:
            if not isinstance(item, dict):
                continue
            num = int(item.get("episode") or 0)
            new_eps.append(
                {
                    "episodeNumber": num,
                    "title": item.get("title") or "",
                    "oneLineSummary": item.get("hook") or item.get("title") or "",
                    "scenes": item.get("scenes") or [],
                    "keyDialogues": item.get("key_dialogues") or [],
                    "tensionLevel": item.get("tension_level"),
                }
            )
        by_num = {
            int(ep.get("episodeNumber")): ep
            for ep in (merged.get("episodes") or [])
            if isinstance(ep, dict) and ep.get("episodeNumber")
        }
        for ep in new_eps:
            prev = by_num.get(ep["episodeNumber"]) or {}
            by_num[ep["episodeNumber"]] = {**prev, **ep}
        merged["episodes"] = sorted(by_num.values(), key=lambda x: x["episodeNumber"])
        merged.setdefault("projectId", str(project.id))
        merged.setdefault("totalEpisodes", _resolve_episode_count(project, brief))
        save_artifact(project, "series_outline", merged)
        artifact_key = "series_outline"
        filled = len([e for e in merged["episodes"] if (e.get("oneLineSummary") or "").strip()])
        _mark_skill_has_content(project, node_index, f"{filled} 集大纲")

    elif skill_id == "creation.script":
        existing = get_artifact(project, "episode_scripts") or {}
        merged = dict(existing)
        by_num = {
            int(ep.get("episodeNumber")): ep
            for ep in (merged.get("episodes") or [])
            if isinstance(ep, dict) and ep.get("episodeNumber")
        }
        for item in skill_data.get("scripts") or []:
            if not isinstance(item, dict):
                continue
            num = int(item.get("episode") or 0)
            content = item.get("content") or item.get("scriptMarkdown") or ""
            prev = by_num.get(num) or {}
            by_num[num] = {
                **prev,
                "episodeNumber": num,
                "title": item.get("title") or prev.get("title") or "",
                "scriptMarkdown": content[:50000],
                "wordCount": len(content),
            }
        merged["episodes"] = sorted(by_num.values(), key=lambda x: x["episodeNumber"])
        merged.setdefault("projectId", str(project.id))
        save_artifact(project, "episode_scripts", merged)
        artifact_key = "episode_scripts"
        _mark_skill_has_content(project, node_index, f"{len(merged['episodes'])} 集剧本")

    elif skill_id == "creation.review":
        save_artifact(project, "review_report", skill_data)
        artifact_key = "review_report"
        score = skill_data.get("overall_score")
        _mark_skill_has_content(
            project,
            node_index,
            f"质检评分 {score}" if score is not None else "质检完成",
        )

    elif skill_id == "creation.polish":
        existing = get_artifact(project, "episode_scripts") or {}
        merged = dict(existing)
        by_num = {
            int(ep.get("episodeNumber")): ep
            for ep in (merged.get("episodes") or [])
            if isinstance(ep, dict) and ep.get("episodeNumber")
        }
        for item in skill_data.get("polished_scripts") or []:
            if not isinstance(item, dict):
                continue
            num = int(item.get("episode") or 0)
            content = item.get("content") or ""
            prev = by_num.get(num) or {}
            by_num[num] = {
                **prev,
                "episodeNumber": num,
                "title": item.get("title") or prev.get("title") or "",
                "scriptMarkdown": content[:50000],
                "wordCount": len(content),
            }
        merged["episodes"] = sorted(by_num.values(), key=lambda x: x["episodeNumber"])
        save_artifact(project, "episode_scripts", merged)
        save_artifact(
            project,
            "polish_log",
            {"polishedAt": timezone.now().isoformat(), "raw": skill_data},
        )
        artifact_key = "episode_scripts"
        _mark_skill_has_content(project, node_index, "润色完成")

    return artifact_key
