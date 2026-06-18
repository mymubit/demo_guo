# -*- coding: utf-8 -*-
"""技能工作台：C 端可编辑视图（受控字段，非完整 Schema 暴露）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import re

from django.conf import settings

from django.utils import timezone

from apps.billing.services import BillingService

from ..artifact_service import get_artifact, save_artifact
from ..models import CreationNode, Project
from ..step_mode import artifact_key_for_node
from ..display.character_display import build_character_bible_view
from ..display.portal_display import (
    portal_gate_log,
    portal_sanitize_character_bible_view,
    portal_sanitize_script_episode,
)
from ..outline_skeleton import (
    OUTLINE_EPISODE_BEAT_MAX,
    OUTLINE_SUMMARY_MIN,
    OUTLINE_SUMMARY_MAX,
    build_outline_skeleton,
    clip_summary_text,
    episodes_needing_summary,
    expand_legacy_episode_summaries,
    outline_stage_blocks,
    stage_rough_outline_ready,
)
from ..display.structure_display import (
    build_structure_plan_view,
    structure_act_count as _payload_act_count,
    structure_reversal_text,
    structure_worldview_summary,
)

_ACT_LABELS = ("起", "承", "转", "合")

_STORY_BRIEF_SPECS = (
    ("idea", ("一句话梗概", "一句话创意", "核心创意", "梗概")),
    ("coreConflict", ("核心冲突",)),
    ("emotionalTone", ("情绪基调",)),
    ("openingHooks", ("前三集钩子", "前三集", "开篇钩子")),
)


def _parse_story_brief(text: str) -> dict:
    result = {key: "" for key, _ in _STORY_BRIEF_SPECS}
    raw = (text or "").strip()
    if not raw:
        return result

    normalized = re.sub(r"\*\*([^*]+)\*\*", r"\1", raw.replace("\r\n", "\n"))
    current_key = None
    in_preamble = True
    buffers = {key: [] for key, _ in _STORY_BRIEF_SPECS}

    for line in normalized.split("\n"):
        stripped = line.strip()
        if not stripped:
            if in_preamble and buffers["idea"]:
                buffers["idea"].append("")
            elif current_key:
                buffers[current_key].append("")
            continue

        matched_key = None
        inline_value = ""
        for key, labels in _STORY_BRIEF_SPECS:
            for label in labels:
                m = re.match(rf"^{re.escape(label)}\s*[：:]\s*(.*)$", stripped)
                if m:
                    matched_key = key
                    inline_value = m.group(1) or ""
                    break
                if stripped == label:
                    matched_key = key
                    break
            if matched_key:
                break

        if matched_key:
            in_preamble = False
            current_key = matched_key
            if inline_value:
                buffers[matched_key].append(inline_value)
            continue

        if in_preamble:
            buffers["idea"].append(line.rstrip())
            continue

        if current_key:
            buffers[current_key].append(line.rstrip())

    for key, _ in _STORY_BRIEF_SPECS:
        result[key] = "\n".join(buffers[key]).strip()

    if not any(result.values()):
        result["idea"] = normalized[:500]
    return result


def _compose_core_idea(story: dict) -> str:
    hook = (story.get("idea") or "").strip()
    conflict = (story.get("coreConflict") or "").strip()
    tone = (story.get("emotionalTone") or "").strip()
    hooks = (story.get("openingHooks") or "").strip()
    if not conflict and not tone and not hooks:
        return hook
    parts = []
    if hook:
        parts.append(hook)
    if conflict:
        parts.append(f"核心冲突：{conflict}")
    if tone:
        parts.append(f"情绪基调：{tone}")
    if hooks:
        parts.append(f"前三集钩子：{hooks}")
    return "\n\n".join(parts)


def _story_brief_from_payload(payload: dict) -> dict:
    core = (payload.get("coreHook") or payload.get("coreIdea") or "").strip()
    wb = payload.get("writingBrief")
    if isinstance(wb, dict):
        mapped = {
            "idea": (wb.get("idea") or wb.get("hook") or "").strip(),
            "coreConflict": (wb.get("coreConflict") or wb.get("core_conflict") or "").strip(),
            "emotionalTone": (wb.get("emotionalTone") or wb.get("tone") or wb.get("emotional_tone") or "").strip(),
            "openingHooks": (wb.get("openingHooks") or wb.get("opening_hooks") or "").strip(),
        }
        if any(mapped.values()):
            if not mapped["idea"] and core:
                parsed = _parse_story_brief(core)
                if parsed.get("idea"):
                    mapped["idea"] = parsed["idea"]
            return mapped
    return _parse_story_brief(core)


def _text_field(key: str, label: str, value: str, *, multiline: bool = False) -> dict:
    return {
        "key": key,
        "label": label,
        "value": value or "",
        "type": "textarea" if multiline else "text",
    }


def _episode_navigation(total: int, act_count: int = 4) -> List[dict]:
    total = max(1, int(total or 1))
    act_count = max(1, min(act_count, len(_ACT_LABELS)))
    chunk = max(1, (total + act_count - 1) // act_count)
    nav: List[dict] = []
    for i in range(act_count):
        start = i * chunk + 1
        if start > total:
            break
        end = min(start + chunk - 1, total)
        label = _ACT_LABELS[i] if i < len(_ACT_LABELS) else f"第{i + 1}幕"
        nav.append(
            {
                "label": label,
                "from_episode": start,
                "to_episode": end,
            }
        )
    return nav


def _structure_act_count(project: Project) -> int:
    structure = get_artifact(project, "structure_plan") or {}
    count = _payload_act_count(structure, fallback=0)
    return count if count else 4


def _normalize_characters(payload: dict) -> List[dict]:
    rows: List[dict] = []
    chars = payload.get("characters") or []
    if isinstance(chars, list) and chars:
        for c in chars:
            if not isinstance(c, dict):
                continue
            rows.append(
                {
                    "id": c.get("characterId") or c.get("id") or c.get("name") or "",
                    "name": c.get("name") or "",
                    "roleType": c.get("roleType") or c.get("role") or "",
                    "oneLineSummary": c.get("oneLineSummary") or c.get("summary") or "",
                    "personality": c.get("personality") or c.get("traits") or "",
                    "background": c.get("background") or c.get("backstory") or "",
                }
            )
        return rows

    role_map = (
        ("protagonist", "主角"),
        ("antagonist", "对立"),
        ("supporting", "配角"),
    )
    for key, label in role_map:
        for c in payload.get(key + "s") or payload.get(key) or []:
            if isinstance(c, dict):
                rows.append(
                    {
                        "id": c.get("id") or c.get("name") or "",
                        "name": c.get("name") or "",
                        "roleType": c.get("roleType") or label,
                        "oneLineSummary": c.get("oneLineSummary") or c.get("summary") or "",
                        "personality": c.get("personality") or "",
                        "background": c.get("background") or "",
                    }
                )
            elif isinstance(c, str):
                rows.append(
                    {
                        "id": c,
                        "name": c,
                        "roleType": label,
                        "oneLineSummary": "",
                        "personality": "",
                        "background": "",
                    }
                )
    return rows




def _outline_episode_slot(episode_number: int, *, filled: bool = False, source: Optional[dict] = None) -> dict:
    src = source if isinstance(source, dict) else {}
    chars = src.get("keyCharacters") or []
    if not isinstance(chars, list):
        chars = []
    stage = src.get("stageInfo") if isinstance(src.get("stageInfo"), dict) else {}
    hook_code = (src.get("hookTypeCode") or "")[:80]
    reversal_code = (src.get("reversalCode") or "")[:80]
    from apps.creation.reference_library import resolve_episode_reference_labels

    ref_labels = resolve_episode_reference_labels(hook_code, reversal_code)
    return {
        "episodeNumber": int(episode_number),
        "title": (src.get("title") or "")[:30],
        "oneLineSummary": clip_summary_text(
            src.get("oneLineSummary") or src.get("summary") or "",
            OUTLINE_SUMMARY_MAX,
        ),
        "hook": (src.get("hook") or "")[:OUTLINE_EPISODE_BEAT_MAX],
        "reversal": (src.get("reversal") or "")[:OUTLINE_EPISODE_BEAT_MAX],
        "cliffhanger": (src.get("cliffhanger") or "")[:OUTLINE_EPISODE_BEAT_MAX],
        "emotionalIntensity": src.get("emotionalIntensity"),
        "keyCharacters": [str(c) for c in chars if c][:5],
        "sceneCount": src.get("sceneCount"),
        "hookTypeCode": hook_code,
        "reversalCode": reversal_code,
        **ref_labels,
        "isKeyEpisode": bool(src.get("isKeyEpisode")),
        "keyEpisodeType": (src.get("keyEpisodeType") or "")[:40],
        "notes": (src.get("notes") or "")[:500],
        "stageInfo": stage,
        "filled": filled,
    }


def _outline_episode_to_artifact(ep: dict, *, prev: Optional[dict] = None) -> dict:
    base = dict(prev) if isinstance(prev, dict) else {}
    summary = clip_summary_text(ep.get("oneLineSummary") or "", OUTLINE_SUMMARY_MAX)
    if summary and len(summary) < OUTLINE_SUMMARY_MIN:
        raise ValueError(f"第 {ep.get('episodeNumber')} 集梗概须 {OUTLINE_SUMMARY_MIN}-{OUTLINE_SUMMARY_MAX} 字")
    chars = ep.get("keyCharacters") or base.get("keyCharacters") or []
    if not isinstance(chars, list):
        chars = [s.strip() for s in str(chars).replace("，", ",").split(",") if s.strip()]
    try:
        intensity = ep.get("emotionalIntensity")
        emotional_intensity = int(intensity) if intensity not in (None, "") else base.get("emotionalIntensity")
    except (TypeError, ValueError):
        emotional_intensity = base.get("emotionalIntensity")
    try:
        scene_raw = ep.get("sceneCount")
        scene_count = int(scene_raw) if scene_raw not in (None, "") else base.get("sceneCount")
    except (TypeError, ValueError):
        scene_count = base.get("sceneCount")
    return {
        **base,
        "episodeNumber": int(ep.get("episodeNumber") or base.get("episodeNumber") or 1),
        "title": (ep.get("title") or base.get("title") or "")[:30],
        "oneLineSummary": summary,
        "hook": (ep.get("hook") or base.get("hook") or "")[:OUTLINE_EPISODE_BEAT_MAX],
        "reversal": (ep.get("reversal") or base.get("reversal") or "")[:OUTLINE_EPISODE_BEAT_MAX],
        "cliffhanger": (ep.get("cliffhanger") or base.get("cliffhanger") or "")[:OUTLINE_EPISODE_BEAT_MAX],
        "emotionalIntensity": emotional_intensity,
        "keyCharacters": [str(c) for c in chars if c][:5],
        "sceneCount": scene_count,
        "hookTypeCode": ep.get("hookTypeCode") or base.get("hookTypeCode") or None,
        "reversalCode": ep.get("reversalCode") or base.get("reversalCode") or None,
        "isKeyEpisode": bool(ep.get("isKeyEpisode")) if "isKeyEpisode" in ep else base.get("isKeyEpisode"),
        "keyEpisodeType": (ep.get("keyEpisodeType") or base.get("keyEpisodeType") or None),
        "notes": (ep.get("notes") or base.get("notes") or "")[:500] or None,
        "stageInfo": base.get("stageInfo") if isinstance(base.get("stageInfo"), dict) else ep.get("stageInfo"),
    }


def build_editor_view(project: Project, node_index: int, *, read_only: bool = False) -> Optional[dict]:
    key = artifact_key_for_node(node_index)
    if not key:
        return None
    payload = get_artifact(project, key) or {}
    total_eps = int(project.episode_count or 80)
    act_count = _structure_act_count(project)
    navigation = _episode_navigation(total_eps, act_count)

    if node_index == 1:
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
            audience = ta
        story = _story_brief_from_payload(payload)
        core_hook = (payload.get("coreHook") or payload.get("coreIdea") or project.core_idea or "").strip()
        return {
            "mode": "brief",
            "editable": True,
            "storyBrief": story,
            "meta": {
                "themeDisplayName": payload.get("themeDisplayName") or payload.get("theme") or project.theme,
                "episodeCount": payload.get("episodeCount") or project.episode_count,
                "formatVariantDisplayName": payload.get("formatVariantDisplayName") or payload.get("formatVariant") or "",
                "targetPlatform": payload.get("targetPlatform") or getattr(project, "target_platform", "") or "",
                "episodeDurationMinutes": payload.get("episodeDurationMinutes"),
                "budgetLevel": payload.get("budgetLevel") or getattr(project, "budget_level", "") or "",
                "creationEntry": payload.get("creationEntry") or getattr(project, "creation_entry", "") or "",
            },
            "trendFormula": payload.get("trendFormula") if isinstance(payload.get("trendFormula"), dict) else None,
            "themeRecommendations": payload.get("themeRecommendations") if isinstance(payload.get("themeRecommendations"), list) else [],
            "writingBrief": payload.get("writingBrief") if isinstance(payload.get("writingBrief"), dict) else None,
            "fields": [
                _text_field("themeDisplayName", "题材", payload.get("themeDisplayName") or payload.get("theme") or project.theme),
                _text_field("episodeCount", "集数", str(payload.get("episodeCount") or project.episode_count)),
                _text_field("targetAudience", "目标受众", audience, multiline=True),
                _text_field("coreHook", "故事策划", core_hook, multiline=True),
                _text_field("referenceWork", "参考作品", payload.get("referenceWork") or project.reference_work or ""),
                _text_field("notes", "备注", payload.get("notes") or "", multiline=True),
            ],
        }

    if node_index == 2:
        if not payload:
            return None
        from ..display.structure_display import normalize_structure_payload

        payload = normalize_structure_payload(dict(payload), project)
        plan_view = build_structure_plan_view(payload, project)
        worldview = payload.get("worldview") or {}
        setting = plan_view["worldview"]["settingSummary"]
        reversals = structure_reversal_text(payload)
        act_count = _payload_act_count(payload, fallback=6)
        return {
            "mode": "structure",
            "editable": True,
            "navigation": navigation,
            "structurePlan": plan_view,
            "fields": [
                _text_field("workingTitle", "建议剧名", plan_view["workingTitle"]),
                _text_field("totalEpisodes", "总集数", str(plan_view["totalEpisodes"])),
                _text_field("worldviewSummary", "世界观", setting, multiline=True),
                _text_field(
                    "timePeriod",
                    "时代背景",
                    plan_view["worldview"]["timePeriod"],
                ),
                _text_field("actCount", "幕结构阶段数", str(act_count or "")),
                _text_field("reversalPoints", "反转点", reversals, multiline=True),
            ],
        }

    if node_index == 3:
        if not payload:
            return None
        bible_view = portal_sanitize_character_bible_view(build_character_bible_view(payload))
        from .workspace_content import resolve_character_gate_log

        gate = portal_gate_log(resolve_character_gate_log(payload))
        return {
            "mode": "characters",
            "editable": True,
            "characterBible": bible_view,
            "relationshipSummary": bible_view["relationshipSummary"],
            "characters": bible_view["characters"],
            "characterGateLog": gate,
        }

    if node_index == 4:
        from ..outline_enrichment import enrich_outline_payload

        structure_plan = get_artifact(project, "structure_plan") or {}
        payload, fixed_summaries = expand_legacy_episode_summaries(payload)
        if fixed_summaries and not read_only:
            save_artifact(project, "series_outline", payload)
        if not payload.get("stageBlocks"):
            payload = build_outline_skeleton(
                project,
                existing=payload or None,
                structure_plan=structure_plan,
            )
        total_eps = int(payload.get("totalEpisodes") or project.episode_count or 80)
        payload = enrich_outline_payload(
            dict(payload),
            structure_plan=structure_plan,
            total_episodes=total_eps,
        )
        navigation = outline_stage_blocks(payload, total_eps, structure_plan=structure_plan)
        stage_blocks = payload.get("stageBlocks") or navigation
        eps_in = payload.get("episodes") or []
        episodes = []
        for ep in eps_in:
            if not isinstance(ep, dict):
                continue
            n = ep.get("episodeNumber") or ep.get("episode")
            episodes.append(
                _outline_episode_slot(
                    int(n) if n else len(episodes) + 1,
                    filled=True,
                    source=ep,
                )
            )
        filled_nums = {e["episodeNumber"] for e in episodes}
        episode_slots = list(episodes)
        for n in range(1, total_eps + 1):
            if n not in filled_nums:
                episode_slots.append(_outline_episode_slot(n, filled=False))
        episode_slots.sort(key=lambda e: e["episodeNumber"])
        framework_ready = stage_rough_outline_ready(payload) or _outline_framework_ready(payload)
        node_cost = BillingService.get_node_coin_cost(4)
        next_start = 1
        while next_start in filled_nums and next_start <= total_eps:
            next_start += 1
        next_end = next_start if next_start <= total_eps else 0
        next_block = None
        for block in navigation:
            start = int(block.get("from_episode") or block.get("fromEpisode") or 1)
            end = int(block.get("to_episode") or block.get("toEpisode") or start)
            block_nums = set(range(start, end + 1))
            missing = sorted(n for n in block_nums if n not in filled_nums)
            if missing:
                next_block = {
                    **block,
                    "from_episode": missing[0],
                    "to_episode": missing[-1],
                    "count": len(missing),
                    "coin_cost": node_cost,
                }
                break
        try:
            fill_all_from, fill_all_to, fill_all_cost = compute_outline_fill_all_range(project)
            fill_all = {
                "from_episode": fill_all_from,
                "to_episode": fill_all_to,
                "count": fill_all_to - fill_all_from + 1,
                "coin_cost": fill_all_cost,
            }
        except ValueError:
            fill_all = {"from_episode": 0, "to_episode": 0, "count": 0, "coin_cost": node_cost}
        return {
            "mode": "outline",
            "editable": True,
            "skeletonReady": True,
            "frameworkReady": framework_ready,
            "stageBlocks": stage_blocks,
            "roughOutline": (payload.get("roughOutline") or payload.get("coarseOutline") or payload.get("structureSummary") or "").strip(),
            "totalEpisodes": total_eps,
            "filledEpisodeCount": len(episodes),
            "navigation": navigation,
            "episodes": episode_slots,
            "nextEpisode": {
                "from_episode": next_start,
                "to_episode": next_end,
                "count": 1 if next_end else 0,
                "coin_cost": node_cost,
            },
            "nextBlock": next_block or {"from_episode": 0, "to_episode": 0, "count": 0, "coin_cost": node_cost},
            "fillAll": fill_all,
            "frameworkCoinCost": node_cost,
            "summaryGaps": episodes_needing_summary(payload),
            "summaryMinLength": OUTLINE_SUMMARY_MIN,
            "summaryMaxLength": OUTLINE_SUMMARY_MAX,
            "creativePlan": payload.get("creativePlan") if isinstance(payload.get("creativePlan"), dict) else {},
            "stageIndex": payload.get("stageIndex") if isinstance(payload.get("stageIndex"), list) else [],
            "keyHighlights": payload.get("keyHighlights") if isinstance(payload.get("keyHighlights"), list) else [],
            "structureSummary": (payload.get("structureSummary") or "").strip(),
            "keyEpisodeIndex": payload.get("keyEpisodeIndex") if isinstance(payload.get("keyEpisodeIndex"), list) else [],
            "planValidationLog": portal_gate_log(
                payload.get("planValidationLog")
                if isinstance(payload.get("planValidationLog"), dict)
                else {}
            ),
        }

    if node_index == 5:
        from ..script_normalizer import apply_script_normalizer

        brief = get_artifact(project, "project_brief") or {}
        payload, _ = apply_script_normalizer(payload, brief)
        eps_in = payload.get("episodes") or []
        episodes = []
        for ep in eps_in:
            if not isinstance(ep, dict):
                continue
            n = ep.get("episodeNumber") or ep.get("episode")
            gate = ep.get("gateLog") if isinstance(ep.get("gateLog"), dict) else {}
            notes = ep.get("polishRevisionNotes") if isinstance(ep.get("polishRevisionNotes"), list) else []
            episodes.append(
                portal_sanitize_script_episode(
                    {
                        "episodeNumber": int(n) if n else len(episodes) + 1,
                        "title": ep.get("title") or "",
                        "scriptMarkdown": ep.get("scriptMarkdown") or ep.get("full_script_text") or "",
                        "wordCount": ep.get("wordCount") or 0,
                        "sceneCount": ep.get("sceneCount") or len(ep.get("scenes") or []),
                        "gateLog": gate,
                        "gatePassed": gate.get("passed") if gate else None,
                        "polishRevisionNotes": notes,
                        "hasPolishNotes": bool(notes),
                    }
                )
            )
        batch = max(1, int(getattr(settings, "FUSION_LLM_EPISODE_BATCH", 2)))
        node_cost = BillingService.get_node_coin_cost(5)
        generated = len(episodes)
        next_start = 1
        if episodes:
            next_start = max(e.get("episodeNumber", 0) for e in episodes) + 1
        next_end = min(next_start + batch - 1, total_eps)
        return {
            "mode": "scripts",
            "editable": True,
            "totalEpisodes": total_eps,
            "generatedCount": generated,
            "navigation": navigation,
            "episodes": episodes,
            "batchSize": batch,
            "batchCoinCost": node_cost,
            "nextBatch": {
                "from_episode": next_start,
                "to_episode": next_end,
                "count": max(0, next_end - next_start + 1) if next_start <= total_eps else 0,
                "coin_cost": node_cost,
            },
            "creatorQualityGuardLog": portal_gate_log(
                payload.get("creatorQualityGuardLog")
                if isinstance(payload.get("creatorQualityGuardLog"), dict)
                else {}
            ),
        }

    return None


def apply_editor_save(project: Project, node_index: int, data: dict) -> dict:
    key = artifact_key_for_node(node_index)
    if not key:
        raise ValueError("无效技能")
    payload = dict(get_artifact(project, key) or {})

    if node_index == 1:
        fields = {f["key"]: f.get("value", "") for f in data.get("fields") or [] if isinstance(f, dict)}
        story_in = data.get("storyBrief") if isinstance(data.get("storyBrief"), dict) else {}
        if story_in:
            composed = _compose_core_idea(story_in)
            if composed:
                fields["coreHook"] = composed
                payload["writingBrief"] = {
                    "idea": (story_in.get("idea") or "")[:500],
                    "coreConflict": (story_in.get("coreConflict") or "")[:500],
                    "emotionalTone": (story_in.get("emotionalTone") or "")[:80],
                    "openingHooks": (story_in.get("openingHooks") or "")[:800],
                }
        if fields.get("coreHook"):
            payload["coreHook"] = fields["coreHook"][:2000]
            payload["coreIdea"] = fields["coreHook"][:2000]
            project.core_idea = fields["coreHook"][:1000]
        if fields.get("targetAudience"):
            ta = payload.get("targetAudience")
            if isinstance(ta, dict):
                ta = {**ta, "description": fields["targetAudience"][:500]}
            else:
                ta = {"description": fields["targetAudience"][:500]}
            payload["targetAudience"] = ta
            project.audience = fields["targetAudience"][:200]
        if fields.get("referenceWork") is not None:
            payload["referenceWork"] = str(fields["referenceWork"])[:500]
            project.reference_work = str(fields["referenceWork"])[:200]
        if fields.get("notes") is not None:
            payload["notes"] = str(fields["notes"])[:500]
        if fields.get("themeDisplayName") is not None:
            theme_name = str(fields["themeDisplayName"]).strip()[:200]
            if theme_name:
                payload["themeDisplayName"] = theme_name
        if fields.get("episodeCount") is not None:
            try:
                ep_count = int(str(fields["episodeCount"]).strip())
                if ep_count > 0:
                    payload["episodeCount"] = ep_count
                    project.episode_count = ep_count
            except (TypeError, ValueError):
                pass
        save_artifact(project, key, payload)
        project.save(update_fields=["title", "core_idea", "audience", "reference_work", "episode_count", "updated_at"])
        _mark_skill_has_content(project, 1, "立项整理已更新")
        return payload

    if node_index == 2:
        sp = data.get("structurePlan") if isinstance(data.get("structurePlan"), dict) else {}
        fields = {f["key"]: f.get("value", "") for f in data.get("fields") or [] if isinstance(f, dict)}
        if sp:
            if sp.get("workingTitle"):
                payload["workingTitle"] = str(sp["workingTitle"])[:200]
            if sp.get("totalEpisodes"):
                try:
                    payload["totalEpisodes"] = int(sp["totalEpisodes"])
                except (TypeError, ValueError):
                    pass
            wv_in = sp.get("worldview") if isinstance(sp.get("worldview"), dict) else {}
            worldview = dict(payload.get("worldview") or {})
            if wv_in.get("settingSummary") is not None:
                worldview["settingSummary"] = str(wv_in["settingSummary"])[:4000]
            if wv_in.get("timePeriod") is not None:
                worldview["timePeriod"] = str(wv_in["timePeriod"])[:100]
            if wv_in.get("rootRules") is not None:
                rules = wv_in.get("rootRules")
                if isinstance(rules, list):
                    worldview["rootRules"] = [str(r)[:500] for r in rules if str(r).strip()]
            payload["worldview"] = worldview
            arc_in = sp.get("coreStoryArc") if isinstance(sp.get("coreStoryArc"), dict) else {}
            if arc_in:
                arc = dict(payload.get("coreStoryArc") or {})
                for key in ("openingSetup", "escalation", "midpointTwist", "finalConfrontation", "resolution"):
                    if arc_in.get(key) is not None:
                        arc[key] = str(arc_in[key])[:2000]
                payload["coreStoryArc"] = arc

            stages_in = sp.get("sixStagePlan") or []
            if isinstance(stages_in, list) and stages_in:
                existing_stages = payload.get("sixStagePlan") or []
                patch_by_idx = {
                    s.get("stageIndex"): s for s in stages_in if isinstance(s, dict) and s.get("stageIndex")
                }
                merged_stages = []
                for stage in existing_stages:
                    if not isinstance(stage, dict):
                        continue
                    patch = patch_by_idx.get(stage.get("stageIndex"))
                    if not patch:
                        merged_stages.append(stage)
                        continue
                    out = dict(stage)
                    for key in ("stageName", "coreTask", "primaryTheme"):
                        if patch.get(key) is not None:
                            out[key] = str(patch[key])[:2000]
                    merged_stages.append(out)
                payload["sixStagePlan"] = merged_stages

            rhythm_in = sp.get("rhythmCurve") or []
            if isinstance(rhythm_in, list) and rhythm_in:
                from ..display.structure_display import normalize_rhythm_block

                existing_rhythm = payload.get("rhythmCurve") or []
                patch_by_range: dict[str, dict] = {}
                for r in rhythm_in:
                    if not isinstance(r, dict):
                        continue
                    normalized = normalize_rhythm_block(dict(r))
                    key = (normalized.get("episodeRange") or "").strip()
                    if key:
                        patch_by_range[key] = normalized
                merged_rhythm: list[dict] = []
                seen: set[str] = set()
                for block in existing_rhythm:
                    if not isinstance(block, dict):
                        continue
                    normalized = normalize_rhythm_block(dict(block))
                    key = (normalized.get("episodeRange") or "").strip()
                    patch = patch_by_range.get(key) if key else None
                    out = dict(normalized)
                    if patch:
                        if patch.get("notes") is not None:
                            out["notes"] = str(patch["notes"])[:500]
                        events = patch.get("keyEvents")
                        if isinstance(events, list):
                            out["keyEvents"] = [str(e)[:200] for e in events if str(e).strip()]
                        if patch.get("intensityLevel") is not None:
                            out["intensityLevel"] = patch["intensityLevel"]
                    if key:
                        if key in seen:
                            continue
                        seen.add(key)
                    merged_rhythm.append(out)
                for key, patch in patch_by_range.items():
                    if key not in seen:
                        merged_rhythm.append(patch)
                        seen.add(key)
                payload["rhythmCurve"] = merged_rhythm

            rev_in = sp.get("keyReversalPoints") or []
            if isinstance(rev_in, list) and rev_in:
                existing_rev = payload.get("keyReversalPoints") or []
                patch_by_ep = {
                    r.get("episodeNumber"): r for r in rev_in if isinstance(r, dict) and r.get("episodeNumber")
                }
                merged_rev = []
                for rev in existing_rev:
                    if not isinstance(rev, dict):
                        continue
                    patch = patch_by_ep.get(rev.get("episodeNumber"))
                    if not patch:
                        merged_rev.append(rev)
                        continue
                    out = dict(rev)
                    if patch.get("description") is not None:
                        out["description"] = str(patch["description"])[:2000]
                    merged_rev.append(out)
                payload["keyReversalPoints"] = merged_rev
        else:
            if fields.get("workingTitle"):
                payload["workingTitle"] = fields["workingTitle"][:200]
            if fields.get("totalEpisodes"):
                try:
                    payload["totalEpisodes"] = int(fields["totalEpisodes"])
                except (TypeError, ValueError):
                    pass
            worldview = dict(payload.get("worldview") or {})
            if fields.get("worldviewSummary") is not None:
                worldview["settingSummary"] = str(fields["worldviewSummary"])[:4000]
            if fields.get("timePeriod"):
                worldview["timePeriod"] = str(fields["timePeriod"])[:100]
            payload["worldview"] = worldview
        save_artifact(project, key, payload)
        from ..display.structure_display import sync_project_title_from_structure

        sync_project_title_from_structure(project, payload)
        _mark_skill_has_content(project, 2, "结构与世界观已保存")
        return payload

    if node_index == 3:
        bible_in = data.get("characterBible") if isinstance(data.get("characterBible"), dict) else {}
        if bible_in.get("summary") is not None:
            payload["summary"] = str(bible_in["summary"])[:2000]

        rel = (bible_in.get("relationshipSummary") or data.get("relationshipSummary") or "").strip()
        if rel:
            payload["relationshipSummary"] = rel[:2000]

        edits = {c.get("id"): c for c in (bible_in.get("characters") or data.get("characters") or []) if isinstance(c, dict) and c.get("id")}

        def _patch_char(char: dict) -> dict:
            cid = char.get("id") or char.get("characterId")
            patch = edits.get(cid)
            if not patch:
                return char
            out = dict(char)
            for field, limit in (
                ("name", 100),
                ("oneLineSummary", 500),
                ("personality", 500),
                ("background", 2000),
                ("appearance", 500),
                ("coreMotivation", 500),
                ("shortTermGoal", 500),
                ("longTermGoal", 500),
                ("weakness", 500),
                ("secret", 500),
                ("surfacePersonality", 500),
                ("realPersonality", 500),
            ):
                if patch.get(field) is not None:
                    out[field] = str(patch[field])[:limit]
            if patch.get("personality") is not None and patch.get("surfacePersonality") is None:
                out["surfacePersonality"] = str(patch["personality"])[:500]
            arc_in = patch.get("characterArc")
            if isinstance(arc_in, dict):
                arc = dict(out.get("characterArc") or {})
                for key in ("startingState", "finalState"):
                    if arc_in.get(key) is not None:
                        arc[key] = str(arc_in[key])[:2000]
                if arc_in.get("keyTurningPoints") is not None:
                    pts = arc_in.get("keyTurningPoints")
                    if isinstance(pts, list):
                        arc["keyTurningPoints"] = [str(p)[:500] for p in pts if str(p).strip()]
                out["characterArc"] = arc
            return out

        for bucket in ("protagonists", "antagonists", "supportingRoles"):
            items = payload.get(bucket)
            if isinstance(items, list):
                payload[bucket] = [_patch_char(c) for c in items if isinstance(c, dict)]

        from ..orchestration.agent_detection import run_character_gate

        payload["characterGateLog"] = run_character_gate(payload)
        save_artifact(project, key, payload)
        count = build_character_bible_view(payload)["characterCount"]
        _mark_skill_has_content(project, 3, f"人物小传 · {count} 人")
        return payload

    if node_index == 4:
        structure_plan = get_artifact(project, "structure_plan") or {}
        if not payload.get("stageBlocks"):
            payload = build_outline_skeleton(
                project,
                existing=payload or None,
                structure_plan=structure_plan,
            )
        blocks_in = data.get("stageBlocks") if isinstance(data.get("stageBlocks"), list) else []
        if blocks_in:
            by_key = {
                b.get("key"): b for b in (payload.get("stageBlocks") or []) if isinstance(b, dict)
            }
            merged_blocks = []
            for block in blocks_in:
                if not isinstance(block, dict):
                    continue
                key = block.get("key")
                prev = by_key.get(key) or {}
                merged_blocks.append(
                    {
                        **prev,
                        **block,
                        "roughOutline": (block.get("roughOutline") or prev.get("roughOutline") or "")[:3000],
                        "fromEpisode": int(
                            block.get("fromEpisode")
                            or block.get("from_episode")
                            or prev.get("fromEpisode")
                            or 1
                        ),
                        "toEpisode": int(
                            block.get("toEpisode")
                            or block.get("to_episode")
                            or prev.get("toEpisode")
                            or 1
                        ),
                    }
                )
            payload["stageBlocks"] = merged_blocks
        payload["roughOutline"] = (data.get("roughOutline") or "")[:3000]
        eps_in = data.get("episodes") or []
        prev_by_num = {
            int(e["episodeNumber"]): e
            for e in (payload.get("episodes") or [])
            if isinstance(e, dict) and e.get("episodeNumber") is not None
        }
        out_eps = []
        for ep in eps_in:
            if not isinstance(ep, dict):
                continue
            if ep.get("filled") is False and not (ep.get("oneLineSummary") or ep.get("title")):
                continue
            try:
                num = int(ep.get("episodeNumber") or len(out_eps) + 1)
            except (TypeError, ValueError):
                num = len(out_eps) + 1
            out_eps.append(_outline_episode_to_artifact(ep, prev=prev_by_num.get(num)))
        payload["episodes"] = sorted(out_eps, key=lambda x: x["episodeNumber"])
        payload["totalEpisodes"] = int(data.get("totalEpisodes") or len(out_eps) or project.episode_count)
        save_artifact(project, key, payload)
        filled = len(payload.get("episodes") or [])
        _mark_skill_has_content(project, 4, f"{filled} 集大纲 · 六阶段")
        return payload

    if node_index == 5:
        eps_in = data.get("episodes") or []
        existing = {e["episodeNumber"]: e for e in (payload.get("episodes") or []) if isinstance(e, dict) and e.get("episodeNumber")}
        for ep in eps_in:
            if not isinstance(ep, dict):
                continue
            try:
                num = int(ep.get("episodeNumber"))
            except (TypeError, ValueError):
                continue
            prev = existing.get(num) or {}
            md = (ep.get("scriptMarkdown") or "")[:50000]
            existing[num] = {
                **prev,
                "episodeNumber": num,
                "title": (ep.get("title") or prev.get("title") or "")[:120],
                "scriptMarkdown": md,
                "wordCount": len(md),
                "sceneCount": prev.get("sceneCount") or 0,
            }
        payload["episodes"] = sorted(existing.values(), key=lambda x: x["episodeNumber"])
        save_artifact(project, key, payload)
        _mark_skill_has_content(project, 5, f"{len(payload['episodes'])} 集剧本")
        from ..script_delivery import persist_script_works
        from ..step_mode import build_pipeline_result_from_project

        try:
            persist_script_works(project, build_pipeline_result_from_project(project))
        except Exception:  # noqa: BLE001
            pass
        return payload

    raise ValueError("不支持保存该技能")


def _mark_skill_has_content(project: Project, node_index: int, summary: str) -> None:
    now = timezone.now()
    CreationNode.objects.filter(project=project, node_index=node_index).update(
        status=CreationNode.STATUS_COMPLETED,
        summary_text=summary[:500],
        completed_at=now,
    )


def _outline_framework_ready(payload: dict) -> bool:
    if stage_rough_outline_ready(payload):
        return True
    if not isinstance(payload, dict):
        return False
    if payload.get("stageIndex") or payload.get("creativePlan"):
        return True
    rough = (payload.get("roughOutline") or payload.get("structureSummary") or "").strip()
    return len(rough) >= 10


def _outline_episode_has_content(ep: dict) -> bool:
    if not isinstance(ep, dict):
        return False
    return bool((ep.get("oneLineSummary") or ep.get("summary") or "").strip())


def compute_outline_batch_range(
    project: Project,
    *,
    from_episode: Optional[int] = None,
    to_episode: Optional[int] = None,
    batch_size: Optional[int] = None,
    block_from: Optional[int] = None,
    block_to: Optional[int] = None,
) -> Tuple[int, int, int]:
    """返回 (from, to, coin_cost)。"""
    total = int(project.episode_count or 80)
    outline = get_artifact(project, "series_outline") or {}
    existing_nums = {
        int(e.get("episodeNumber"))
        for e in (outline.get("episodes") or [])
        if isinstance(e, dict) and e.get("episodeNumber") and _outline_episode_has_content(e)
    }
    default_batch = max(1, int(getattr(settings, "FUSION_LLM_OUTLINE_BATCH", 1)))
    batch = max(1, int(batch_size or default_batch))

    search_start = max(1, int(block_from)) if block_from else 1
    search_end = min(int(block_to), total) if block_to else total

    if from_episode is None:
        start = search_start
        while start in existing_nums and start <= search_end:
            start += 1
        if start > search_end:
            raise ValueError("当前区块集纲已全部生成")
        from_episode = start
    else:
        from_episode = max(search_start, int(from_episode))

    if to_episode is None:
        to_episode = min(from_episode + batch - 1, search_end, total)
    else:
        to_episode = min(int(to_episode), search_end, total)

    if from_episode > to_episode:
        raise ValueError("无效的集数范围")

    cost = BillingService.get_node_coin_cost(4)
    return from_episode, to_episode, cost


def compute_outline_fill_all_range(project: Project) -> Tuple[int, int, int]:
    """生成全部剩余集纲的范围。"""
    total = int(project.episode_count or 80)
    outline = get_artifact(project, "series_outline") or {}
    existing_nums = {
        int(e.get("episodeNumber"))
        for e in (outline.get("episodes") or [])
        if isinstance(e, dict) and e.get("episodeNumber") and _outline_episode_has_content(e)
    }
    start = 1
    while start in existing_nums and start <= total:
        start += 1
    if start > total:
        raise ValueError("全部集纲已生成完毕")
    cost = BillingService.get_node_coin_cost(4)
    return start, total, cost


def compute_script_batch_range(
    project: Project,
    *,
    from_episode: Optional[int] = None,
    to_episode: Optional[int] = None,
    batch_size: Optional[int] = None,
) -> Tuple[int, int, int]:
    """返回 (from, to, coin_cost)。"""
    total = int(project.episode_count or 80)
    scripts = get_artifact(project, "episode_scripts") or {}
    existing_nums = {
        int(e.get("episodeNumber"))
        for e in (scripts.get("episodes") or [])
        if isinstance(e, dict) and e.get("episodeNumber")
    }
    default_batch = max(1, int(getattr(settings, "FUSION_LLM_EPISODE_BATCH", 5)))
    batch = max(1, int(batch_size or default_batch))

    if from_episode is None:
        start = 1
        while start in existing_nums and start <= total:
            start += 1
        if start > total:
            raise ValueError("全部集数剧本已生成")
        from_episode = start
    else:
        from_episode = max(1, int(from_episode))

    if to_episode is None:
        to_episode = min(from_episode + batch - 1, total)
    else:
        to_episode = min(int(to_episode), total)

    if from_episode > to_episode:
        raise ValueError("无效的集数范围")

    count = to_episode - from_episode + 1
    unit = BillingService.get_node_coin_cost(5)
    cost = unit
    return from_episode, to_episode, cost


ARTIFACT_KEY_TO_NODE_INDEX = {
    "project_brief": 1,
    "structure_plan": 2,
    "character_bible": 3,
    "series_outline": 4,
    "episode_scripts": 5,
}


def build_artifact_editor_view(project: Project, artifact_key: str) -> Optional[dict]:
    """将 artifact payload 转为 C 端结构化预览视图（只读，不写库）。"""
    payload = get_artifact(project, artifact_key)
    if payload is None:
        return None
    node_index = ARTIFACT_KEY_TO_NODE_INDEX.get(str(artifact_key))
    if node_index is not None:
        view = build_editor_view(project, node_index, read_only=True)
        if view is not None:
            view["editable"] = False
            return view
    return {"mode": "json", "payload": payload, "editable": False}
