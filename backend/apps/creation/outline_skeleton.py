# -*- coding: utf-8 -*-
"""分集大纲骨架：立项确认集数后预搭建六阶段 + 分集槽位。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .artifact_service import get_artifact, save_artifact
from .models import Project

_STAGE_DEFS = (
    ("qi", "起", 1),
    ("cheng", "承", 2),
    ("zhuan", "转", 3),
    ("he", "合", 4),
)

_SCHEMA_STAGE_NAMES = (
    "阶段1：开篇期",
    "阶段2：矛盾升级期",
    "阶段3：中段转折期",
    "阶段4：情绪爆发期",
    "阶段5：终极对决期",
    "阶段6：结局收尾期",
)


def build_four_act_blocks(total_episodes: int) -> List[dict]:
    """起承转合四段（遗留兼容）。"""
    total = max(1, int(total_episodes or 1))
    chunk = max(1, (total + 3) // 4)
    blocks: List[dict] = []
    start = 1
    for idx, (key, label, stage_index) in enumerate(_STAGE_DEFS):
        if start > total:
            break
        end = min(start + chunk - 1, total) if idx < 3 else total
        blocks.append(
            {
                "key": key,
                "label": label,
                "stageIndex": stage_index,
                "fromEpisode": start,
                "toEpisode": end,
                "from_episode": start,
                "to_episode": end,
                "roughOutline": "",
            }
        )
        start = end + 1
    if blocks:
        blocks[-1]["toEpisode"] = total
        blocks[-1]["to_episode"] = total
    return blocks


def build_six_stage_blocks(
    total_episodes: int,
    six_stage_plan: Optional[List[dict]] = None,
) -> List[dict]:
    """六阶段分段：优先 structure_plan.sixStagePlan，否则均分六段。"""
    total = max(1, int(total_episodes or 1))
    if isinstance(six_stage_plan, list) and len(six_stage_plan) >= 6:
        blocks: List[dict] = []
        for item in six_stage_plan[:6]:
            if not isinstance(item, dict):
                continue
            stage_index = int(item.get("stageIndex") or len(blocks) + 1)
            start = int(item.get("startEpisode") or 1)
            end = int(item.get("endEpisode") or start)
            stage_name = (item.get("stageName") or "").strip()
            label = stage_name.split("：")[-1] if "：" in stage_name else (stage_name or f"阶段{stage_index}")
            blocks.append(
                {
                    "key": f"stage{stage_index}",
                    "label": label,
                    "stageIndex": stage_index,
                    "fromEpisode": start,
                    "toEpisode": end,
                    "from_episode": start,
                    "to_episode": end,
                    "roughOutline": (item.get("coreTask") or "")[:3000],
                    "coreTask": (item.get("coreTask") or "")[:500],
                }
            )
        if len(blocks) >= 6:
            blocks[-1]["toEpisode"] = max(blocks[-1]["toEpisode"], total)
            blocks[-1]["to_episode"] = blocks[-1]["toEpisode"]
            return blocks

    chunk = max(1, (total + 5) // 6)
    blocks = []
    start = 1
    for stage_index in range(1, 7):
        if start > total:
            break
        end = min(start + chunk - 1, total) if stage_index < 6 else total
        name = _SCHEMA_STAGE_NAMES[stage_index - 1]
        label = name.split("：")[-1]
        blocks.append(
            {
                "key": f"stage{stage_index}",
                "label": label,
                "stageIndex": stage_index,
                "fromEpisode": start,
                "toEpisode": end,
                "from_episode": start,
                "to_episode": end,
                "roughOutline": "",
            }
        )
        start = end + 1
    if blocks:
        blocks[-1]["toEpisode"] = total
        blocks[-1]["to_episode"] = total
    return blocks


def _resolve_structure_plan(
    project: Project,
    structure_plan: Optional[dict] = None,
) -> dict:
    if isinstance(structure_plan, dict) and structure_plan:
        return structure_plan
    return get_artifact(project, "structure_plan") or {}


def _stage_index_from_blocks(blocks: List[dict]) -> List[dict]:
    stage_index: List[dict] = []
    for block in blocks:
        idx = int(block.get("stageIndex") or 0)
        schema_name = (
            _SCHEMA_STAGE_NAMES[idx - 1]
            if 1 <= idx <= len(_SCHEMA_STAGE_NAMES)
            else f"阶段{idx}"
        )
        stage_index.append(
            {
                "stageIndex": idx,
                "stageName": schema_name,
                "startEpisode": block["fromEpisode"],
                "endEpisode": block["toEpisode"],
                "episodeCount": block["toEpisode"] - block["fromEpisode"] + 1,
            }
        )
    return stage_index


def build_outline_skeleton(
    project: Project,
    *,
    existing: Optional[dict] = None,
    structure_plan: Optional[dict] = None,
) -> dict:
    """生成分集大纲空骨架（不覆盖已有粗纲/集纲）。"""
    total = int(project.episode_count or 80)
    base = dict(existing or {})
    blocks_in = base.get("stageBlocks") if isinstance(base.get("stageBlocks"), list) else None

    structure = _resolve_structure_plan(project, structure_plan)
    six_plan = structure.get("sixStagePlan")

    if blocks_in:
        stage_blocks_source = blocks_in
    else:
        stage_blocks_source = build_six_stage_blocks(total, six_plan)

    merged_blocks: List[dict] = []
    for block in stage_blocks_source:
        if not isinstance(block, dict):
            continue
        merged_blocks.append(
            {
                "key": block.get("key") or "",
                "label": block.get("label") or "",
                "stageIndex": block.get("stageIndex") or block.get("stage_index") or 0,
                "fromEpisode": int(block.get("fromEpisode") or block.get("from_episode") or 1),
                "toEpisode": int(block.get("toEpisode") or block.get("to_episode") or 1),
                "from_episode": int(block.get("fromEpisode") or block.get("from_episode") or 1),
                "to_episode": int(block.get("toEpisode") or block.get("to_episode") or 1),
                "roughOutline": (block.get("roughOutline") or "")[:3000],
                "coreTask": (block.get("coreTask") or "")[:500],
            }
        )
    if not merged_blocks:
        merged_blocks = build_six_stage_blocks(total, six_plan)

    stage_index = base.get("stageIndex") or _stage_index_from_blocks(merged_blocks)

    episodes = [
        e for e in (base.get("episodes") or []) if isinstance(e, dict) and e.get("episodeNumber")
    ]

    return {
        "nodeId": "node-4-outline",
        "nodeName": "大纲与创作规划节点",
        "totalEpisodes": total,
        "skeletonReady": True,
        "stageBlocks": merged_blocks,
        "stageIndex": stage_index,
        "episodes": episodes,
        "roughOutline": (base.get("roughOutline") or "")[:3000],
        "creativePlan": base.get("creativePlan") or {},
        "keyHighlights": base.get("keyHighlights") or [],
    }


def _should_rebuild_skeleton(
    existing: dict,
    project: Project,
    structure_plan: Optional[dict] = None,
) -> bool:
    if not existing.get("stageBlocks"):
        return True
    if int(existing.get("totalEpisodes") or 0) != int(project.episode_count or 0):
        return True
    blocks = existing.get("stageBlocks") or []
    structure = _resolve_structure_plan(project, structure_plan)
    six = structure.get("sixStagePlan")
    if isinstance(six, list) and len(six) >= 6 and len(blocks) < 6:
        return True
    return False


def ensure_outline_skeleton(
    project: Project,
    *,
    persist: bool = True,
    structure_plan: Optional[dict] = None,
) -> dict:
    """立项后写入 series_outline 骨架（已有则合并保留内容）。"""
    existing = get_artifact(project, "series_outline") or {}
    if not _should_rebuild_skeleton(existing, project, structure_plan):
        return existing
    payload = build_outline_skeleton(
        project,
        existing=existing if existing else None,
        structure_plan=structure_plan,
    )
    if persist:
        save_artifact(project, "series_outline", payload)
    return payload


def outline_stage_blocks(
    payload: Optional[dict],
    total_episodes: int,
    *,
    structure_plan: Optional[dict] = None,
) -> List[dict]:
    if isinstance(payload, dict) and payload.get("stageBlocks"):
        return payload["stageBlocks"]
    six = (structure_plan or {}).get("sixStagePlan")
    return build_six_stage_blocks(total_episodes, six)


def stage_rough_outline_ready(payload: dict) -> bool:
    blocks = outline_stage_blocks(payload, payload.get("totalEpisodes") or 0)
    return any(len((b.get("roughOutline") or "").strip()) >= 20 for b in blocks)


OUTLINE_SUMMARY_MIN = 100
OUTLINE_SUMMARY_MAX = 400
OUTLINE_EPISODE_BEAT_MAX = 500


def clip_summary_text(text: str, max_len: int = OUTLINE_SUMMARY_MAX) -> str:
    """截断梗概时在句号/逗号等边界切，避免句中硬切。"""
    raw = (text or "").strip()
    if len(raw) <= max_len:
        return raw
    chunk = raw[:max_len]
    min_pos = int(max_len * 0.55)
    for sep in ("。", "！", "？", "；", "，", ".", "!", "?", ";", ","):
        idx = chunk.rfind(sep)
        if idx >= min_pos:
            return chunk[: idx + 1].strip()
    return chunk.strip()


def episodes_needing_summary(payload: Optional[dict]) -> List[int]:
    """旧项目或短梗概：返回须补全至 100–400 字的集号。"""
    if not isinstance(payload, dict):
        return []
    gaps: List[int] = []
    for ep in payload.get("episodes") or []:
        if not isinstance(ep, dict):
            continue
        if ep.get("filled") is False:
            continue
        num = ep.get("episodeNumber") or ep.get("episode")
        if num is None:
            continue
        summary = (ep.get("oneLineSummary") or ep.get("summary") or "").strip()
        if not summary:
            continue
        if len(summary) < OUTLINE_SUMMARY_MIN:
            gaps.append(int(num))
    return sorted(gaps)


def _expand_episode_summary(ep: dict) -> str:
    summary = (ep.get("oneLineSummary") or ep.get("summary") or "").strip()
    if len(summary) >= OUTLINE_SUMMARY_MIN:
        return clip_summary_text(summary, OUTLINE_SUMMARY_MAX)
    parts: List[str] = []
    if summary:
        parts.append(summary)
    title = (ep.get("title") or "").strip()
    if title and title not in summary:
        parts.append(title)
    for key in ("hook", "reversal", "cliffhanger", "notes"):
        val = (ep.get(key) or "").strip()
        if val and val not in " ".join(parts):
            parts.append(val)
    merged = "，".join(p for p in parts if p)
    num = ep.get("episodeNumber") or ep.get("episode") or "?"
    pad = (
        f"第{num}集沿主线推进：人物在冲突中做出关键抉择，情绪张力逐级抬升，"
        f"并以集末悬念承接下一集，具体场戏与对白在剧本阶段展开。"
    )
    if not merged:
        merged = pad
    elif len(merged) < OUTLINE_SUMMARY_MIN:
        merged = f"{merged}。{pad}"
    while len(merged) < OUTLINE_SUMMARY_MIN and len(merged) < OUTLINE_SUMMARY_MAX:
        merged = f"{merged}主线持续升级，悬念与反转节奏对齐六阶段规划。"
    return clip_summary_text(merged, OUTLINE_SUMMARY_MAX)


def expand_legacy_episode_summaries(payload: Optional[dict]) -> tuple[dict, List[int]]:
    """旧四段大纲等短梗概：合并字段扩写至 100–400 字，返回 (payload, 已修复集号)。"""
    if not isinstance(payload, dict):
        return {}, []
    fixed: List[int] = []
    for ep in payload.get("episodes") or []:
        if not isinstance(ep, dict) or ep.get("filled") is False:
            continue
        num = ep.get("episodeNumber") or ep.get("episode")
        if num is None:
            continue
        summary = (ep.get("oneLineSummary") or ep.get("summary") or "").strip()
        if not summary or len(summary) >= OUTLINE_SUMMARY_MIN:
            continue
        expanded = _expand_episode_summary(ep)
        if len(expanded) >= OUTLINE_SUMMARY_MIN:
            ep["oneLineSummary"] = expanded
            ep.pop("summary", None)
            fixed.append(int(num))
    return payload, sorted(fixed)


def merge_stage_blocks(existing: dict, chunk: dict) -> dict:
    out = dict(existing)
    incoming = chunk.get("stageBlocks") or []
    if not isinstance(incoming, list) or not incoming:
        return out
    by_key = {b.get("key"): b for b in (out.get("stageBlocks") or []) if isinstance(b, dict)}
    merged: List[dict] = []
    for item in incoming:
        if not isinstance(item, dict):
            continue
        key = item.get("key") or item.get("label")
        prev = by_key.get(key) or {}
        merged.append(
            {
                "key": item.get("key") or prev.get("key") or "",
                "label": item.get("label") or prev.get("label") or "",
                "stageIndex": item.get("stageIndex") or prev.get("stageIndex") or 0,
                "fromEpisode": int(
                    item.get("fromEpisode")
                    or item.get("from_episode")
                    or prev.get("fromEpisode")
                    or prev.get("from_episode")
                    or 1
                ),
                "toEpisode": int(
                    item.get("toEpisode")
                    or item.get("to_episode")
                    or prev.get("toEpisode")
                    or prev.get("to_episode")
                    or 1
                ),
                "from_episode": int(
                    item.get("fromEpisode")
                    or item.get("from_episode")
                    or prev.get("from_episode")
                    or 1
                ),
                "to_episode": int(
                    item.get("toEpisode")
                    or item.get("to_episode")
                    or prev.get("to_episode")
                    or 1
                ),
                "roughOutline": (item.get("roughOutline") or prev.get("roughOutline") or "")[:3000],
                "coreTask": (item.get("coreTask") or prev.get("coreTask") or "")[:500],
            }
        )
    out["stageBlocks"] = merged
    if merged and not out.get("stageIndex"):
        out["stageIndex"] = _stage_index_from_blocks(merged)
    return out
