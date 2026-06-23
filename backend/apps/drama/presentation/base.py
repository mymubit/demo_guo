# -*- coding: utf-8 -*-
"""Drama 产物展示公共构建块。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from apps.drama.presentation.blocks_builder import dicts_to_cards
from apps.drama.presentation.text_localize import (
    format_inline_dict,
    localize_phrase_label,
    localize_role_label,
    parse_enumerated_prose,
    relationship_type_label,
)
from apps.drama.presentation.labels import ARTIFACT_LABELS, FIELD_LABELS
from apps.drama.presentation.normalize import format_scalar, normalize_payload

_SCENE_HEADER_RE = re.compile(r"^\d+-\d+")
_DIALOGUE_RE = re.compile(r"^.+（.+）：")
_MEMORY_CHECKPOINT_RE = re.compile(r"^记忆检查点[：:]?\s*")
_DIALOGUE_COLON_RE = re.compile(r"^([^：:\n△【\d][^：:]{0,18})[：:](.+)$")


def label(key: str) -> str:
    if not key:
        return ""
    if key in FIELD_LABELS:
        return FIELD_LABELS[key]
    if key in ARTIFACT_LABELS:
        return ARTIFACT_LABELS[key]
    # 已是中文键（含 phase_1 等混合键外的纯中文）
    if any("\u4e00" <= char <= "\u9fff" for char in key):
        return key
    episode_match = re.match(r"^episode_(\d+)$", key, re.IGNORECASE)
    if episode_match:
        return f"第{episode_match.group(1)}集"
    # 禁止把未映射的 snake_case 直接暴露为 UI 文案
    normalized = key.replace("-", "_")
    if normalized in FIELD_LABELS:
        return FIELD_LABELS[normalized]
    return FIELD_LABELS.get(key.replace(" ", "_"), key.replace("_", " "))


def summary_from_blocks(blocks: List[dict], fallback: str = "") -> str:
    for block in blocks:
        if block.get("type") == "hero" and block.get("subtitle"):
            return str(block["subtitle"])[:240]
        if block.get("type") == "paragraph" and block.get("text"):
            return str(block["text"])[:240]
        if block.get("type") == "verdict" and block.get("detail"):
            return str(block["detail"])[:240]
    return fallback[:240] if fallback else ""


def view(artifact_key: str, schema_version: str, blocks: List[dict], *, summary: str = "") -> dict:
    return {
        "artifact_key": artifact_key,
        "schema_version": schema_version,
        "label": ARTIFACT_LABELS.get(artifact_key) or artifact_key,
        "summary": summary or summary_from_blocks(blocks),
        "blocks": blocks,
    }


def kv_block(title: str, rows: List[dict], *, layout: str = "") -> dict:
    block: dict = {"type": "kv", "title": title, "rows": rows}
    if layout:
        block["layout"] = layout
    return block


def paragraph_block(title: str, text: str) -> dict:
    return {"type": "paragraph", "title": title, "text": text}


def list_block(title: str, items: List[str]) -> dict:
    return {"type": "list", "title": title, "items": items}


def cards_block(title: str, items: List[dict]) -> dict:
    return {"type": "cards", "title": title, "items": items}


def steps_block(title: str, items: List[dict]) -> dict:
    return {"type": "steps", "title": title, "items": items}


def stage_outlines_block(title: str, stages: List[dict]) -> dict:
    return {"type": "stage_outlines", "title": title, "stages": stages}


def metrics_block(title: str, items: List[dict]) -> dict:
    return {"type": "metrics", "title": title, "items": items}


def outline_overview_block(
    *,
    total_episodes: Any = None,
    checks: Optional[List[dict]] = None,
    reverse_points: Optional[List[dict]] = None,
) -> dict:
    """系列大纲顶部概览：总集数、节奏校验、A 级反转点。"""
    total = None
    if total_episodes not in (None, "", [], {}):
        total = format_scalar(total_episodes)
    return {
        "type": "outline_overview",
        "total_episodes": total,
        "checks": checks or [],
        "reverse_points": reverse_points or [],
    }


def verdict_block(title: str, *, passed: bool, detail: str, issues: Optional[List[str]] = None) -> dict:
    return {
        "type": "verdict",
        "title": title,
        "passed": passed,
        "detail": detail,
        "issues": issues or [],
    }


def score_board_block(
    title: str,
    *,
    grade: str = "",
    total: Any = None,
    summary: str = "",
    dimensions: Optional[List[dict]] = None,
) -> dict:
    return {
        "type": "score_board",
        "title": title,
        "grade": grade,
        "total": total,
        "summary": summary,
        "dimensions": dimensions or [],
    }


def checks_block(title: str, *, passed: bool, verdict: str, items: List[dict]) -> dict:
    return {
        "type": "checks",
        "title": title,
        "passed": passed,
        "verdict": verdict,
        "items": items,
    }


def script_episodes_block(title: str, episodes: List[dict]) -> dict:
    return {"type": "script_episodes", "title": title, "episodes": episodes}


def plan_overview_block(
    title: str,
    *,
    hero_text: str = "",
    metrics: Optional[List[dict]] = None,
    checks: Optional[List[dict]] = None,
) -> dict:
    return {
        "type": "plan_overview",
        "title": title,
        "hero_text": hero_text,
        "metrics": metrics or [],
        "checks": checks or [],
    }


def plan_items_block(title: str, items: List[dict]) -> dict:
    return {"type": "plan_items", "title": title, "items": items}


def character_roster_block(characters: List[dict]) -> dict:
    return {"type": "character_roster", "characters": characters}


def relationship_graph_block(items: List[dict]) -> dict:
    return {"type": "relationship_graph", "items": items}


def world_sections_block(sections: List[dict]) -> dict:
    return {"type": "world_sections", "sections": sections}


def assessment_report_block(
    title: str,
    *,
    passed: bool | None = None,
    metrics: Optional[List[dict]] = None,
    detail: str = "",
    notes: Optional[List[str]] = None,
) -> dict:
    return {
        "type": "assessment_report",
        "title": title,
        "passed": passed,
        "metrics": metrics or [],
        "detail": detail,
        "notes": notes or [],
    }


def episode_metrics_list_block(title: str, episodes: List[dict]) -> dict:
    return {"type": "episode_metrics_list", "title": title, "episodes": episodes}


def deliverable_sections_block(title: str, sections: List[dict]) -> dict:
    return {"type": "deliverable_sections", "title": title, "sections": sections}


def rows_from_dict(data: dict, keys: tuple[str, ...]) -> List[dict]:
    rows = []
    for key in keys:
        val = data.get(key)
        if val not in (None, "", [], {}):
            rows.append({"key": label(key), "value": format_scalar(val)})
    return rows


def append_dict_kv(blocks: List[dict], body: dict, key: str, title: str, field_keys: tuple[str, ...]) -> None:
    section = body.get(key)
    if not isinstance(section, dict):
        return
    rows = rows_from_dict(section, field_keys)
    if rows:
        blocks.append(kv_block(title or label(key), rows))


def append_scalar_kv(blocks: List[dict], body: dict, keys: tuple[str, ...], title: str = "详情") -> None:
    rows = rows_from_dict(body, keys)
    if rows:
        blocks.append(kv_block(title, rows))


def list_block_from_items(title: str, items: Any, *, limit: int = 30) -> dict | None:
    if not isinstance(items, list) or not items:
        return None
    if all(isinstance(x, str) for x in items):
        return list_block(title, [str(x) for x in items[:limit]])
    formatted = format_list_items(items, limit=limit)
    return list_block(title, formatted) if formatted else None


def append_list(blocks: List[dict], body: dict, key: str, title: str = "", *, limit: int = 30) -> None:
    items = body.get(key)
    block = list_block_from_items(title or label(key), items, limit=limit)
    if block:
        blocks.append(block)


def append_cards(blocks: List[dict], body: dict, key: str, title: str = "", *, limit: int = 20) -> None:
    items = body.get(key)
    if isinstance(items, list) and items and all(isinstance(x, dict) for x in items):
        cards = dicts_to_cards([x for x in items if isinstance(x, dict)], limit=limit)
        if cards:
            blocks.append(cards_block(title or label(key), cards))


def append_paragraph(blocks: List[dict], body: dict, key: str, title: str = "") -> None:
    val = body.get(key)
    if isinstance(val, str) and val.strip():
        blocks.append(paragraph_block(title or label(key), val.strip()))


def build_blocks_from_value(title: str, value: Any, depth: int = 0) -> List[dict]:
    if depth > 4:
        return []
    section_title = label(title) if title else ""

    if isinstance(value, str) and value.strip():
        return [paragraph_block(section_title, value.strip())]
    if isinstance(value, (int, float, bool)):
        return [kv_block(section_title or "详情", [{"key": section_title or "值", "value": format_scalar(value)}])]
    if isinstance(value, list):
        if not value:
            return []
        if all(isinstance(x, str) for x in value):
            return [list_block(section_title, [str(x) for x in value[:40]])]
        if all(isinstance(x, dict) for x in value):
            cards = dicts_to_cards([x for x in value if isinstance(x, dict)])
            return [cards_block(section_title, cards)] if cards else []
        return []
    if isinstance(value, dict):
        scalar_rows = []
        nested: List[dict] = []
        for key, sub_val in value.items():
            if isinstance(sub_val, (str, int, float, bool)) and format_scalar(sub_val) != "—":
                scalar_rows.append({"key": label(str(key)), "value": format_scalar(sub_val)})
            elif isinstance(sub_val, list) and sub_val:
                nested.extend(build_blocks_from_value(str(key), sub_val, depth + 1))
            elif isinstance(sub_val, dict) and sub_val:
                nested.extend(build_blocks_from_value(str(key), sub_val, depth + 1))
        blocks: List[dict] = []
        if scalar_rows:
            blocks.append(kv_block(section_title or "详情", scalar_rows))
        blocks.extend(nested)
        return blocks
    return []


def script_episodes_block(title: str, episodes: List[dict], *, total_episodes: int | None = None) -> dict:
    block: dict = {"type": "script_episodes", "title": title, "episodes": episodes}
    if total_episodes is not None:
        block["total_episodes"] = total_episodes
    return block


def review_overview_block(
    *,
    passed: bool | None = None,
    pacing_passed: bool | None = None,
    issue_count: int = 0,
) -> dict:
    return {
        "type": "review_overview",
        "passed": passed,
        "pacing_passed": pacing_passed,
        "issue_count": issue_count,
    }


def review_issues_block(title: str, items: List[dict]) -> dict:
    return {"type": "review_issues", "title": title, "items": items}


def normalize_review_issues(raw: Any) -> List[dict]:
    if not isinstance(raw, list):
        return []
    items: List[dict] = []
    for item in raw[:50]:
        if not isinstance(item, dict):
            continue
        description = str(item.get("description") or "").strip()
        if not description:
            continue
        issue_type = str(item.get("issueType") or "").strip()
        episode_number = item.get("episodeNumber")
        scene_number = str(item.get("sceneNumber") or "").strip()
        entry: dict = {"description": description}
        if issue_type:
            entry["issue_type"] = label(issue_type) if issue_type in FIELD_LABELS else issue_type
        if episode_number not in (None, "", [], {}):
            entry["episode_number"] = format_scalar(episode_number)
        if scene_number:
            entry["scene_number"] = scene_number
        items.append(entry)
    return items


QUALITY_DIMENSION_MAX: dict[str, float] = {
    "格式规范": 15,
    "结构完整性": 20,
    "人物塑造": 15,
    "情绪曲线": 15,
    "对白质量": 15,
    "钩子效果": 10,
    "梦境指标": 5,
    "商业可行性": 5,
}

QUALITY_DIMENSION_ORDER: tuple[str, ...] = (
    "格式规范",
    "结构完整性",
    "人物塑造",
    "情绪曲线",
    "对白质量",
    "钩子效果",
    "梦境指标",
    "商业可行性",
)

QUALITY_DETAIL_DIMENSION_MAP: dict[str, str] = {
    "format_issues": "格式规范",
    "structure_issues": "结构完整性",
    "character_performance": "人物塑造",
    "emotion_curve": "情绪曲线",
    "dialogue_quality": "对白质量",
    "hook_effect": "钩子效果",
    "dream_safety_index": "梦境指标",
    "commercial_potential": "商业可行性",
}


def quality_report_block(
    *,
    rating: str = "",
    total_score: Any = None,
    max_total: float = 100,
    fuse_triggered: bool | None = None,
    dimensions: Optional[List[dict]] = None,
) -> dict:
    return {
        "type": "quality_report",
        "rating": rating,
        "total_score": total_score,
        "max_total": max_total,
        "fuse_triggered": fuse_triggered,
        "dimensions": dimensions or [],
    }


def build_quality_dimensions(scores: Any, details: Any) -> List[dict]:
    if not isinstance(scores, dict):
        return []

    detail_map: dict[str, str] = {}
    if isinstance(details, dict):
        for key, val in details.items():
            text = str(val or "").strip()
            if not text:
                continue
            dim_name = QUALITY_DETAIL_DIMENSION_MAP.get(str(key)) or label(str(key))
            detail_map[dim_name] = text

    raw_dimensions: dict[str, dict] = {}
    for key, score in scores.items():
        if score in (None, "", [], {}):
            continue
        name = label(str(key))
        max_score = QUALITY_DIMENSION_MAX.get(name)
        raw_dimensions[name] = {
            "name": name,
            "score": score,
            "max_score": max_score,
            "detail": detail_map.get(name, ""),
        }

    ordered: List[dict] = []
    for name in QUALITY_DIMENSION_ORDER:
        if name in raw_dimensions:
            ordered.append(raw_dimensions.pop(name))
    for item in raw_dimensions.values():
        ordered.append(item)
    return ordered


def normalize_script_content_lines(content: Any) -> tuple[List[str], str]:
    """将 scriptContent 统一为行列表，并提取正文内的记忆检查点。"""
    raw_lines: List[str] = []
    if isinstance(content, str) and content.strip():
        raw_lines = content.splitlines()
    elif isinstance(content, list):
        raw_lines = [str(line) for line in content]

    script_lines: List[str] = []
    checkpoint_parts: List[str] = []
    for raw in raw_lines:
        line = str(raw).strip()
        if not line:
            continue
        if _MEMORY_CHECKPOINT_RE.match(line):
            text = _MEMORY_CHECKPOINT_RE.sub("", line, count=1).strip()
            if text:
                checkpoint_parts.append(text)
            continue
        script_lines.append(line)
    return script_lines, "；".join(checkpoint_parts)


def _is_scene_header_line(line: str) -> bool:
    if _SCENE_HEADER_RE.match(line):
        return True
    return (
        not line.startswith("△")
        and not line.startswith("【")
        and "：" not in line[:20]
        and ("日" in line or "夜" in line)
        and ("内" in line or "外" in line)
    )


def _is_dialogue_line(line: str) -> bool:
    if line.startswith("△") or line.startswith("【") or _is_scene_header_line(line):
        return False
    if _DIALOGUE_RE.match(line):
        return True
    match = _DIALOGUE_COLON_RE.match(line)
    if not match:
        return False
    left = match.group(1).strip()
    if not left or len(left) > 20:
        return False
    return True


def script_content_to_beats(lines: List[Any]) -> List[dict]:
    beats: List[dict] = []
    for raw in lines:
        line = str(raw).strip()
        if not line:
            continue
        if line.startswith("【") and "金句" in line:
            continue

        if _is_scene_header_line(line):
            beats.append({"sceneHeader": line, "action": "", "dialogue": ""})
        elif line.startswith("△"):
            if beats and not beats[-1]["action"] and not beats[-1]["dialogue"]:
                beats[-1]["action"] = line
            else:
                scene = beats[-1]["sceneHeader"] if beats else ""
                beats.append({"sceneHeader": scene, "action": line, "dialogue": ""})
        elif _is_dialogue_line(line):
            if beats and beats[-1]["dialogue"]:
                beats.append(
                    {
                        "sceneHeader": beats[-1]["sceneHeader"],
                        "action": "",
                        "dialogue": line,
                    }
                )
            elif beats:
                beats[-1]["dialogue"] = line
            else:
                beats.append({"sceneHeader": "", "action": "", "dialogue": line})
        else:
            if beats:
                prev = beats[-1]
                if prev["dialogue"]:
                    beats.append(
                        {
                            "sceneHeader": prev["sceneHeader"],
                            "action": line,
                            "dialogue": "",
                        }
                    )
                elif prev["action"]:
                    prev["action"] += "\n" + line
                else:
                    prev["action"] = line
            else:
                beats.append({"sceneHeader": "", "action": line, "dialogue": ""})
    return beats


def parse_episode_script_content(content: Any) -> tuple[List[dict], str]:
    lines, embedded_checkpoint = normalize_script_content_lines(content)
    beats = script_content_to_beats(lines)
    return beats, embedded_checkpoint


CHARACTER_PROFILE_FIELD_GROUPS: tuple[tuple[str, ...], ...] = (
    ("surface_want", "want"),
    ("deep_need", "need"),
    ("lie",),
    ("flaw",),
    ("ghost",),
    ("character_arc",),
    ("timbre_tag", "voice_tag"),
)


def build_character_id_map(body: dict) -> dict[str, str]:
    """character_id → 姓名，供关系网络展示解析。"""
    id_map: dict[str, str] = {}
    chars = body.get("characters") or []
    if not isinstance(chars, list):
        return id_map
    for char in chars:
        if not isinstance(char, dict):
            continue
        cid = char.get("character_id")
        name = char.get("name")
        if cid and name:
            id_map[str(cid)] = str(name)
    return id_map


CHARACTER_ROLE_KEYS = ("role_position", "identity", "role_type")


def resolve_character_role(char: dict) -> str:
    for key in CHARACTER_ROLE_KEYS:
        val = char.get(key)
        if val in (None, "", [], {}):
            continue
        text = str(val).strip()
        if any("\u4e00" <= ch <= "\u9fff" for ch in text):
            return text
        localized = localize_phrase_label(text) or localize_role_label(text)
        if localized:
            return localized
    return ""


def character_profile_title(char: dict) -> str:
    name = str(char.get("name") or "未命名")
    role = resolve_character_role(char)
    return f"{name} · {role}" if role else name


def _format_character_field_value(key: str, val: Any) -> str:
    if isinstance(val, dict):
        if key in ("arc", "character_arc"):
            parts = []
            for sub_key, sub_val in val.items():
                if sub_val in (None, "", [], {}):
                    continue
                parts.append(f"{label(str(sub_key))}：{format_scalar(sub_val)}")
            if parts:
                return "\n".join(parts)
        formatted = format_inline_dict(val)
        return formatted if formatted else format_scalar(val)
    if isinstance(val, str) and key in ("role_type", "role"):
        localized = localize_role_label(val)
        return localized if localized else format_scalar(val)
    return format_scalar(val)


def character_profile_rows(char: dict) -> List[dict]:
    rows: List[dict] = []
    for aliases in CHARACTER_PROFILE_FIELD_GROUPS:
        for key in aliases:
            val = char.get(key)
            if val not in (None, "", [], {}):
                rows.append({"key": label(key), "value": _format_character_field_value(key, val)})
                break
    return rows


def character_roster_entries(chars: Any) -> List[dict]:
    if not isinstance(chars, list):
        return []
    entries: List[dict] = []
    for char in chars[:20]:
        if not isinstance(char, dict):
            continue
        rows = character_profile_rows(char)
        if not rows:
            continue
        entries.append(
            {
                "title": character_profile_title(char),
                "rows": rows,
            }
        )
    return entries


def relationship_graph_entries(network: Any, *, id_map: dict[str, str] | None = None) -> List[dict]:
    cards = relationship_network_cards(network, id_map=id_map)
    return [
        {
            "title": card["title"],
            "subtitle": card.get("subtitle") or "",
            "body": card.get("body") or "",
        }
        for card in cards
    ]


def relationship_network_cards(network: Any, *, id_map: dict[str, str] | None = None) -> List[dict]:
    if isinstance(network, str) and network.strip():
        return []
    if not isinstance(network, list):
        return []
    cards = []
    resolve = (id_map or {}).get

    def display_ref(ref: Any) -> str:
        text = str(ref or "").strip()
        if not text:
            return ""
        return str(resolve(text, text))

    for item in network[:20]:
        if not isinstance(item, dict):
            continue
        pair = item.get("character_pair") or []
        if isinstance(pair, list) and pair:
            names = [display_ref(x) for x in pair[:2] if display_ref(x)]
            title = " ↔ ".join(names)
        else:
            source = display_ref(item.get("source_id"))
            target = display_ref(item.get("target_id"))
            title = " ↔ ".join(x for x in (source, target) if x)
        if not title:
            title = str(item.get("name") or "关系")
        rel_display = relationship_type_label(item)
        body_parts = [
            str(item.get("core_conflict") or ""),
            str(item.get("interaction_rule") or ""),
        ]
        cards.append(
            {
                "title": title,
                "subtitle": rel_display,
                "body": "\n".join(p for p in body_parts if p)[:800],
            }
        )
    return cards


def storyboard_to_cards(items: List[dict]) -> List[dict]:
    cards = []
    for item in items[:40]:
        if not isinstance(item, dict):
            continue
        shot = item.get("镜号") or item.get("shot_no") or item.get("shotNo") or ""
        scene = item.get("场景") or item.get("scene") or ""
        title = f"镜{shot} · {scene}".strip(" ·") if shot else str(scene or "镜头")
        duration = item.get("时长(MM:SS-MM:SS)") or item.get("duration") or ""
        framing = item.get("景别") or item.get("framing") or ""
        angle = item.get("摄影角度") or item.get("angle") or ""
        subtitle = " · ".join(x for x in (str(framing), str(angle), str(duration)) if x and x != "—")
        body_parts = [
            item.get("画面内容(△开头)") or item.get("画面内容") or item.get("visual") or "",
            item.get("叙事目的") or item.get("purpose") or "",
            item.get("声音") or item.get("audio") or "",
            item.get("备注") or item.get("note") or "",
        ]
        cards.append(
            {
                "title": title,
                "subtitle": subtitle,
                "body": "\n".join(str(p) for p in body_parts if p)[:600],
            }
        )
    return cards


_STAGE_KEY_RE = re.compile(r"^stage_(\d+)$")

_EPISODE_SEGMENT_KEYS = ("opening", "development", "climax", "resolution")


def _episode_segment_sections(segments: Any) -> List[dict]:
    if not isinstance(segments, dict):
        return []
    return [
        {"label": label(key), "text": str(segments[key]).strip()}
        for key in _EPISODE_SEGMENT_KEYS
        if segments.get(key)
    ]


def _episode_emotion_sections(emotion_beat: Any) -> List[dict]:
    if not isinstance(emotion_beat, dict):
        return []
    sections: List[dict] = []
    for key, section_label in (
        ("EV", "情绪高峰 EV"),
        ("ET", "情绪低谷 ET"),
        ("TP", "情节转折 TP"),
    ):
        val = emotion_beat.get(key)
        if val not in (None, "", [], {}):
            sections.append({"label": section_label, "text": str(val).strip()})
    return sections


def a_level_reverse_cards(points: List[dict]) -> List[dict]:
    cards = []
    for item in points[:12]:
        if not isinstance(item, dict):
            continue
        ep_no = item.get("episode_num") or item.get("episode_id") or ""
        content = str(item.get("reverse_content") or "").strip()
        if not content:
            continue
        cards.append(
            {
                "episode": str(ep_no) if ep_no not in (None, "") else "",
                "title": f"第{ep_no}集" if ep_no else "A级反转",
                "text": content[:800],
            }
        )
    return cards


_EPISODE_RANGE_RE = re.compile(r"^(\d+)\s*-\s*(\d+)$")


def parse_episode_range(text: Any) -> tuple[int, int] | None:
    if text in (None, "", [], {}):
        return None
    match = _EPISODE_RANGE_RE.match(str(text).strip())
    if not match:
        return None
    start, end = int(match.group(1)), int(match.group(2))
    if start > end:
        return None
    return start, end


def episode_outline_number(item: dict, *, fallback: int = 1) -> int:
    raw = item.get("episode_id") or item.get("episode_num") or fallback
    try:
        return int(raw)
    except (TypeError, ValueError):
        return fallback


def episode_outline_card_item(item: dict, *, fallback_index: int = 0) -> dict | None:
    if not isinstance(item, dict):
        return None
    ep_no = episode_outline_number(item, fallback=fallback_index + 1)
    ep_name = str(item.get("episode_name") or "").strip()
    hook = str(item.get("ending_hook") or "").strip()
    segments = item.get("four_part_structure")
    structure = _episode_segment_sections(segments)
    emotions = _episode_emotion_sections(item.get("emotion_beat"))
    sections = structure + emotions
    if not sections and not hook:
        return None
    title = f"第{ep_no}集"
    if ep_name:
        title = f"{title} · {ep_name}"
    return {
        "episode_no": ep_no,
        "title": title,
        "subtitle": hook if hook else "",
        "structure": structure,
        "emotions": emotions,
        "sections": sections,
    }


def stage_narrative_definitions(stage_narrative: dict) -> List[dict]:
    """解析带 episode_range 的 six_stage_narrative（stage_N 形态）。"""
    if not isinstance(stage_narrative, dict):
        return []
    stages: List[tuple[int, dict]] = []
    for key, val in stage_narrative.items():
        match = _STAGE_KEY_RE.match(str(key))
        if not match or not isinstance(val, dict):
            continue
        ep_range = parse_episode_range(val.get("episode_range"))
        if not ep_range:
            continue
        start, end = ep_range
        points = val.get("key_plot_points") or []
        highlights = [
            str(point).strip()
            for point in (points if isinstance(points, list) else [])
            if str(point).strip()
        ][:8]
        stages.append(
            (
                int(match.group(1)),
                {
                    "index": int(match.group(1)),
                    "title": str(val.get("stage_name") or f"第{match.group(1)}段").strip(),
                    "subtitle": f"第{start}-{end}集",
                    "episode_start": start,
                    "episode_end": end,
                    "summary": str(val.get("core_goal") or "").strip(),
                    "highlights": highlights,
                },
            )
        )
    stages.sort(key=lambda item: item[0])
    return [item[1] for item in stages]


def build_stage_grouped_outlines(stage_narrative: dict, outlines: List[dict]) -> List[dict]:
    """按六阶段 episode_range 将分集大纲分组。"""
    definitions = stage_narrative_definitions(stage_narrative)
    if not definitions or not isinstance(outlines, list):
        return []

    ep_cards: dict[int, dict] = {}
    for index, item in enumerate(outlines[:40]):
        card = episode_outline_card_item(item, fallback_index=index)
        if card:
            ep_cards[episode_outline_number(item, fallback=index + 1)] = card

    groups: List[dict] = []
    for stage in definitions:
        episodes = [
            ep_cards[ep_no]
            for ep_no in range(stage["episode_start"], stage["episode_end"] + 1)
            if ep_no in ep_cards
        ]
        if not episodes and not stage.get("summary") and not stage.get("highlights"):
            continue
        groups.append(
            {
                "index": stage["index"],
                "title": stage["title"],
                "subtitle": stage["subtitle"],
                "summary": stage.get("summary") or "",
                "highlights": stage.get("highlights") or [],
                "episodes": episodes,
            }
        )
    return groups


def format_deviation_node(node: Any) -> str:
    if not isinstance(node, dict):
        return format_scalar(node)
    idx = node.get("node_index")
    tag = str(node.get("emotion_tag") or "")
    head = f"节点{idx} · {tag}" if idx is not None else tag
    metrics = []
    if node.get("actual_value") is not None:
        metrics.append(f"实际 {format_scalar(node['actual_value'])}")
    if node.get("target_value") is not None:
        metrics.append(f"目标 {format_scalar(node['target_value'])}")
    if node.get("deviation_gap") is not None:
        metrics.append(f"偏差 {format_scalar(node['deviation_gap'])}")
    lines = [head]
    if metrics:
        lines.append(" · ".join(metrics))
    trigger = node.get("trigger_event")
    if trigger:
        lines.append(str(trigger))
    return "\n".join(lines)


def format_emotion_marker(data: Any) -> str:
    if not isinstance(data, dict):
        return format_scalar(data)
    val = data.get("value")
    event = str(data.get("trigger_event") or "").strip()
    if val is not None and event:
        return f"强度 {format_scalar(val)} — {event}"
    if val is not None:
        return f"强度 {format_scalar(val)}"
    return event


def format_emotion_node_line(node: Any) -> str:
    if not isinstance(node, dict):
        return format_scalar(node)
    idx = node.get("node_index")
    tag = str(node.get("emotion_tag") or "")
    val = node.get("actual_value")
    if idx is not None and val is not None:
        return f"节点{idx} {tag}（{format_scalar(val)}）"
    if idx is not None:
        return f"节点{idx} {tag}".strip()
    return tag or format_scalar(val)


def format_list_items(items: List[Any], *, limit: int = 10) -> List[str]:
    """将 list 项格式化为可读字符串，避免 dict 直接 str()。"""
    lines: List[str] = []
    for item in items[:limit]:
        if isinstance(item, dict):
            if {"node_index", "emotion_tag"} & set(item.keys()):
                lines.append(format_deviation_node(item))
            elif {"volume", "emotion", "timestamp"} & set(item.keys()):
                from apps.drama.presentation.text_localize import format_inline_dict

                formatted = format_inline_dict(item)
                if formatted:
                    lines.append(formatted)
            elif item.get("trigger_event") and len(item) <= 3:
                idx = item.get("position_node_index") or item.get("node_index")
                prefix = f"节点{idx} · " if idx is not None else ""
                lines.append(f"{prefix}{item['trigger_event']}")
            else:
                parts = []
                for key, val in item.items():
                    if val in (None, "", [], {}):
                        continue
                    parts.append(f"{label(str(key))}：{format_scalar(val) if not isinstance(val, str) else val}")
                lines.append(" · ".join(parts[:6]) if parts else format_scalar(item))
        else:
            lines.append(str(item))
    return lines


def format_detail_list(value: Any) -> str:
    if isinstance(value, list):
        parts = format_list_items(value, limit=10)
        return "；".join(parts) if parts else "—"
    if isinstance(value, str):
        return value
    return format_scalar(value)


def compliance_passed(verdict: str) -> bool:
    text = str(verdict or "").lower()
    if text in ("approved", "pass", "passed", "通过"):
        return True
    verdict_text = str(verdict or "")
    return "通过" in verdict_text or "符合" in verdict_text or "无违规" in verdict_text


_COMPLIANCE_PASS_STATUS = frozenset(
    {
        "pass",
        "passed",
        "approved",
        "通过",
        "suggest_no_modification",
        "optimize_suggestion",
        "无风险",
    }
)


def normalize_compliance_risk_items(raw: Any) -> List[dict]:
    if not isinstance(raw, list):
        return []
    items: List[dict] = []
    for item in raw[:30]:
        if isinstance(item, str) and item.strip():
            items.append({"description": item.strip()})
            continue
        if not isinstance(item, dict):
            continue
        description = str(
            item.get("description") or item.get("detail") or item.get("message") or ""
        ).strip()
        entry: dict = {}
        if description:
            entry["description"] = description
        for src, dst in (
            ("type", "risk_type"),
            ("risk_type", "risk_type"),
            ("location", "location"),
            ("severity", "severity"),
            ("suggestion", "suggestion"),
        ):
            val = item.get(src)
            if val not in (None, "", [], {}):
                entry[dst] = str(val).strip()
        if entry:
            items.append(entry)
    return items


def _compliance_status_passed(status: Any, *, level: str, items: List[dict]) -> bool:
    if items and level == "P0":
        return False
    if status is None:
        return not items
    text = str(status).strip().lower()
    if text in ("fail", "failed", "reject", "rejected", "不通过", "blocked"):
        return False
    if text in _COMPLIANCE_PASS_STATUS or compliance_passed(str(status)):
        return True
    return not items


def build_compliance_level(body: dict, level: str) -> dict:
    level_lower = level.lower()
    items = normalize_compliance_risk_items(body.get(f"{level_lower}_risk"))
    passed = len(items) == 0
    if level == "P0" and items:
        passed = False
    elif level == "P1" and items:
        passed = False

    status_label = f"{len(items)} 项风险" if items else "通过"
    return {
        "level": level,
        "passed": passed,
        "status": status_label,
        "detail": "",
        "items": items,
    }


def build_compliance_nine_dimension(body: dict) -> dict | None:
    raw = body.get("nine_dimension_risk")
    if not isinstance(raw, list):
        return None
    items = normalize_compliance_risk_items(raw)
    return {"passed": len(items) == 0, "items": items, "dimensions": [], "summary": ""}


def compliance_report_block(
    *,
    passed: bool,
    conclusion: str = "",
    levels: Optional[List[dict]] = None,
    nine_dimension: Optional[dict] = None,
) -> dict:
    return {
        "type": "compliance_report",
        "passed": passed,
        "conclusion": conclusion,
        "levels": levels or [],
        "nine_dimension": nine_dimension,
    }


def build_compliance_report_view(body: dict) -> dict:
    conclusion = str(body.get("overall_conclusion") or "").strip()
    levels = [build_compliance_level(body, level) for level in ("P0", "P1", "P2")]
    nine_dimension = build_compliance_nine_dimension(body)

    passed = compliance_passed(conclusion)
    if "不通过" in conclusion:
        passed = False
    elif not conclusion:
        passed = all(level["passed"] for level in levels)
        if nine_dimension is not None:
            passed = passed and bool(nine_dimension.get("passed", True))

    return compliance_report_block(
        passed=passed,
        conclusion=conclusion,
        levels=levels,
        nine_dimension=nine_dimension,
    )


def dict_to_kv_rows(data: dict, *, key_labels: dict[str, str] | None = None) -> List[dict]:
    rows = []
    for key, val in data.items():
        if val in (None, "", [], {}):
            continue
        row_key = (key_labels or {}).get(str(key)) or label(str(key))
        if isinstance(val, (str, int, float, bool)):
            rows.append({"key": row_key, "value": format_scalar(val)})
        elif isinstance(val, list):
            formatted = format_detail_list(val)
            if formatted != "—":
                rows.append({"key": row_key, "value": formatted})
        elif isinstance(val, dict):
            inner_parts = []
            for sub_k, sub_v in val.items():
                if sub_v in (None, "", [], {}):
                    continue
                sub_label = label(str(sub_k))
                if isinstance(sub_v, (str, int, float, bool)):
                    inner_parts.append(f"{sub_label}：{format_scalar(sub_v)}")
                elif isinstance(sub_v, list):
                    inner_parts.append(f"{sub_label}：{format_detail_list(sub_v)}")
                else:
                    inner_parts.append(f"{sub_label}：{format_scalar(sub_v)}")
            if inner_parts:
                rows.append({"key": row_key, "value": "\n".join(inner_parts)})
    return rows


def append_power_structure(blocks: List[dict], power: Any) -> None:
    """权力结构：兼容 dict / list / 字符串，避免 list 被 str() 挤成一行。"""
    if power in (None, "", [], {}):
        return
    if isinstance(power, dict):
        rows = dict_to_kv_rows(power)
        if rows:
            blocks.append(kv_block("权力结构", rows))
        return
    if isinstance(power, list):
        if all(isinstance(x, str) for x in power):
            blocks.append(list_block("权力结构", [str(x) for x in power[:20]]))
        else:
            items = format_list_items(power, limit=20)
            if items:
                blocks.append(list_block("权力结构", items))
        return
    if isinstance(power, str) and power.strip():
        items = parse_enumerated_prose(power.strip())
        if items:
            _append_text_as_list_or_cards(blocks, "权力结构", items, card_threshold=120, item_label="条目")
        else:
            blocks.append(paragraph_block("权力结构", power.strip()))


def _append_text_as_list_or_cards(
    blocks: List[dict],
    title: str,
    items: List[str],
    *,
    card_threshold: int = 80,
    item_label: str = "场景",
) -> None:
    if not items:
        return
    trimmed = [str(x).strip() for x in items if str(x).strip()][:12]
    if not trimmed:
        return
    if any(len(x) > card_threshold for x in trimmed):
        cards = [
            {"title": f"{item_label} {index + 1}", "subtitle": "", "body": text[:600]}
            for index, text in enumerate(trimmed)
        ]
        blocks.append(cards_block(title, cards))
    else:
        blocks.append(list_block(title, trimmed))


def append_core_spaces(blocks: List[dict], spaces: Any) -> None:
    """核心场景：兼容 core_space / core_spaces、编号长文本、字符串列表与对象列表。"""
    if spaces in (None, "", [], {}):
        return
    if isinstance(spaces, dict):
        spaces = [spaces]
    if isinstance(spaces, str) and spaces.strip():
        items = parse_enumerated_prose(spaces)
        if items:
            _append_text_as_list_or_cards(blocks, "核心场景", items)
        else:
            blocks.append(paragraph_block("核心场景", spaces.strip()))
        return
    if not isinstance(spaces, list) or not spaces:
        return
    if len(spaces) == 1 and isinstance(spaces[0], str):
        items = parse_enumerated_prose(spaces[0])
        if items:
            _append_text_as_list_or_cards(blocks, "核心场景", items)
            return
    if isinstance(spaces[0], str):
        expanded: List[str] = []
        for chunk in spaces[:12]:
            parsed = parse_enumerated_prose(str(chunk), min_items=2)
            if parsed:
                expanded.extend(parsed)
            else:
                expanded.append(str(chunk))
        _append_text_as_list_or_cards(blocks, "核心场景", expanded)
        return
    cards = []
    for space in spaces[:12]:
        if not isinstance(space, dict):
            continue
        cards.append(
            {
                "title": str(space.get("space_name") or space.get("name") or "场景"),
                "subtitle": str(space.get("location") or "")[:80],
                "body": str(
                    space.get("vertical_show_feature")
                    or space.get("description")
                    or space.get("feature")
                    or ""
                )[:500],
            }
        )
    if cards:
        blocks.append(cards_block("核心场景", cards))


def nested_check_rows(data: dict) -> List[dict]:
    """style_drift_detection_result 等 {name: {check_status, detail}} 结构。"""
    rows = []
    for key, val in data.items():
        if not isinstance(val, dict):
            continue
        status = val.get("check_status") or val.get("status") or val.get("level") or ""
        detail = val.get("detail") or val.get("details") or ""
        rows.append({"key": label(str(key)), "value": f"{status} · {detail}".strip(" · ")})
    return rows


def adaptation_breakdown_cards(items: List[dict]) -> List[dict]:
    cards = []
    for item in items[:20]:
        if not isinstance(item, dict):
            continue
        ep_no = item.get("episode_no") or item.get("episode_id") or ""
        title = f"第{ep_no}集" if ep_no else "分集改编"
        body_parts = []
        for key in ("hook_opening", "core_conflict", "cliffhanger"):
            val = item.get(key)
            if val:
                body_parts.append(f"{label(key)}：{val}")
        cards.append({"title": title, "subtitle": "", "body": "\n".join(body_parts)[:500]})
    return cards


def reversal_cards(items: List[dict]) -> List[dict]:
    cards = []
    for item in items[:20]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("reversal_name") or item.get("name") or "反转")
        subtitle = str(item.get("position") or item.get("reversal_id") or "")
        design = item.get("reverse_design") or {}
        body_parts = []
        if isinstance(design, dict):
            for key, val in design.items():
                if isinstance(val, str) and val.strip():
                    body_parts.append(f"{label(str(key))}：{val}")
        cards.append({"title": title, "subtitle": subtitle, "body": "\n".join(body_parts)[:500]})
    return cards


def visual_prompt_episode_blocks(value: list) -> List[dict]:
    blocks: List[dict] = []
    for ep in value[:10]:
        if not isinstance(ep, dict):
            continue
        ep_no = ep.get("episodeNumber")
        prompts = ep.get("scenePrompts")
        if not isinstance(prompts, list):
            continue
        items = []
        for index, prompt in enumerate(prompts[:30]):
            if isinstance(prompt, str):
                items.append({"title": f"场景 {index + 1}", "subtitle": "", "body": prompt[:600]})
            elif isinstance(prompt, dict):
                scene = prompt.get("sceneId") or index + 1
                text = prompt.get("prompt") or ""
                items.append({"title": f"场景 {scene}", "subtitle": "", "body": str(text)[:600]})
        if items:
            blocks.append(cards_block(f"第{ep_no}集视觉提示" if ep_no else "视觉提示", items))
    return blocks


def emotion_externalization_cards(data: dict) -> List[dict]:
    cards = []
    for key, val in (data or {}).items():
        if not isinstance(val, dict):
            continue
        title = str(val.get("emotion_name") or label(str(key)))
        body = "\n".join(
            p
            for p in (
                f"视觉：{val['visual_performance']}" if val.get("visual_performance") else "",
                f"听觉：{val['audio_performance']}" if val.get("audio_performance") else "",
            )
            if p
        )
        cards.append({"title": title, "subtitle": label(str(key)), "body": body[:500]})
    return cards


def qdn_model_metrics(data: dict) -> List[dict]:
    metrics = []
    for key, val in (data or {}).items():
        if not isinstance(val, dict):
            continue
        name = val.get("dimension_name") or label(str(key))
        target = val.get("global_target")
        if target is not None:
            metrics.append({"label": str(name), "value": format_scalar(target)})
    return metrics


__all__ = [
    "normalize_payload",
    "format_scalar",
    "label",
    "view",
    "kv_block",
    "paragraph_block",
    "list_block",
    "cards_block",
    "steps_block",
    "metrics_block",
    "verdict_block",
    "score_board_block",
    "checks_block",
    "script_episodes_block",
    "rows_from_dict",
    "append_dict_kv",
    "append_scalar_kv",
    "append_list",
    "append_cards",
    "append_paragraph",
    "build_blocks_from_value",
    "script_content_to_beats",
    "list_block_from_items",
    "relationship_network_cards",
    "build_character_id_map",
    "character_profile_title",
    "character_profile_rows",
    "append_character_group",
    "resolve_character_role",
    "storyboard_to_cards",
    "format_detail_list",
    "compliance_passed",
]
