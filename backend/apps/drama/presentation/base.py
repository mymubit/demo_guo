# -*- coding: utf-8 -*-
"""Drama 产物展示公共构建块。"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from apps.drama.presentation.blocks_builder import dicts_to_cards
from apps.drama.presentation.labels import ARTIFACT_LABELS, FIELD_LABELS
from apps.drama.presentation.normalize import format_scalar, normalize_payload

_SCENE_HEADER_RE = re.compile(r"^\d+-\d+")
_DIALOGUE_RE = re.compile(r"^.+（.+）：")


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
    # 禁止把未映射的 snake_case 直接暴露为英文 UI 文案
    normalized = key.replace("-", "_")
    if normalized in FIELD_LABELS:
        return FIELD_LABELS[normalized]
    return FIELD_LABELS.get(key.replace(" ", "_"), key)


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


def kv_block(title: str, rows: List[dict]) -> dict:
    return {"type": "kv", "title": title, "rows": rows}


def paragraph_block(title: str, text: str) -> dict:
    return {"type": "paragraph", "title": title, "text": text}


def list_block(title: str, items: List[str]) -> dict:
    return {"type": "list", "title": title, "items": items}


def cards_block(title: str, items: List[dict]) -> dict:
    return {"type": "cards", "title": title, "items": items}


def metrics_block(title: str, items: List[dict]) -> dict:
    return {"type": "metrics", "title": title, "items": items}


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


def append_list(blocks: List[dict], body: dict, key: str, title: str = "", *, limit: int = 30) -> None:
    items = body.get(key)
    if isinstance(items, list) and items:
        if all(isinstance(x, str) for x in items):
            blocks.append(list_block(title or label(key), [str(x) for x in items[:limit]]))
        elif all(isinstance(x, dict) for x in items):
            formatted = format_list_items(items, limit=limit)
            if formatted:
                blocks.append(list_block(title or label(key), formatted))


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


def script_content_to_beats(lines: List[Any]) -> List[dict]:
    beats: List[dict] = []
    for raw in lines:
        line = str(raw).strip()
        if not line:
            continue
        if line.startswith("【") and "金句" in line:
            continue

        is_scene = bool(_SCENE_HEADER_RE.match(line)) or (
            not line.startswith("△")
            and ("日" in line or "夜" in line)
            and ("内" in line or "外" in line)
            and "：" not in line[:20]
        )

        if is_scene:
            beats.append({"sceneHeader": line, "action": "", "dialogue": ""})
        elif line.startswith("△"):
            if beats and not beats[-1]["action"] and not beats[-1]["dialogue"]:
                beats[-1]["action"] = line
            else:
                scene = beats[-1]["sceneHeader"] if beats else ""
                beats.append({"sceneHeader": scene, "action": line, "dialogue": ""})
        elif _DIALOGUE_RE.match(line):
            if beats:
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


def relationship_network_cards(network: Any) -> List[dict]:
    if isinstance(network, str) and network.strip():
        return []
    if not isinstance(network, list):
        return []
    cards = []
    for item in network[:20]:
        if not isinstance(item, dict):
            continue
        pair = item.get("character_pair") or []
        if isinstance(pair, list) and pair:
            title = " ↔ ".join(str(x) for x in pair[:2])
        else:
            source = item.get("source_id") or item.get("source") or item.get("from") or ""
            target = item.get("target_id") or item.get("target") or item.get("to") or ""
            title = f"{source} → {target}".strip(" →")
        if not title:
            title = str(item.get("name") or "关系")
        rel = item.get("relationship_type") or item.get("relation") or item.get("type") or ""
        body_parts = [
            str(item.get("core_conflict") or ""),
            str(item.get("interaction_rule") or item.get("description") or item.get("detail") or ""),
        ]
        cards.append(
            {
                "title": title,
                "subtitle": str(rel) if rel else "",
                "body": "\n".join(p for p in body_parts if p)[:500],
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


def episode_outline_cards(outlines: List[dict]) -> List[dict]:
    cards = []
    for index, item in enumerate(outlines[:30]):
        if not isinstance(item, dict):
            continue
        ep_no = (
            item.get("episode_id")
            or item.get("episode_num")
            or item.get("episodeNumber")
            or item.get("episode_number")
            or index + 1
        )
        ep_name = item.get("episode_name") or item.get("title") or ""
        hook = item.get("end_hook") or item.get("ending_hook") or item.get("hook") or ""
        segments = (
            item.get("four_segment_structure")
            or item.get("four_part_structure")
            or {}
        )
        body_parts = []
        if isinstance(segments, dict):
            for seg_key in ("opening", "development", "climax", "closing"):
                seg_val = segments.get(seg_key)
                if seg_val:
                    body_parts.append(f"{label(seg_key)}：{seg_val}")
        markers = item.get("emotion_markers") or {}
        if isinstance(markers, dict) and markers.get("TP_plot_turning_point"):
            body_parts.append(f"转折点：{markers['TP_plot_turning_point']}")
        tp = item.get("TP") or item.get("turning_point") or item.get("summary") or ""
        if tp and not body_parts:
            body_parts.append(str(tp))
        title = f"第{ep_no}集"
        if ep_name:
            title = f"{title} · {ep_name}"
        cards.append(
            {
                "title": title,
                "subtitle": str(hook)[:120] if hook else "",
                "body": "\n".join(body_parts)[:500],
            }
        )
    return cards


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
    return text in ("approved", "pass", "passed", "通过") or "通过" in str(verdict)


def dict_to_kv_rows(data: dict, *, key_labels: dict[str, str] | None = None) -> List[dict]:
    rows = []
    for key, val in data.items():
        if val in (None, "", [], {}):
            continue
        if isinstance(val, (str, int, float, bool)):
            row_key = (key_labels or {}).get(str(key)) or label(str(key))
            rows.append({"key": row_key, "value": format_scalar(val)})
    return rows


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


def phase_narrative_cards(data: dict) -> List[dict]:
    cards = []
    if not isinstance(data, dict):
        return cards
    # expert: phase_1..phase_6；fast: establish_world, conflict_intro 等
    ordered = []
    for key in sorted(data.keys()):
        if key.startswith("phase_"):
            ordered.append((key, data[key]))
    if not ordered:
        for key, val in data.items():
            ordered.append((key, val))
    for key, val in ordered[:12]:
        if isinstance(val, dict):
            phase_name = val.get("phase_name") or label(str(key))
            content = val.get("core_content") or val.get("content") or ""
            cards.append({"title": str(phase_name), "subtitle": label(str(key)), "body": str(content)[:500]})
        elif isinstance(val, str) and val.strip():
            cards.append({"title": label(str(key)), "subtitle": "", "body": val.strip()[:500]})
    return cards


def visual_prompt_episode_blocks(value: list) -> List[dict]:
    blocks: List[dict] = []
    for ep in value[:10]:
        if not isinstance(ep, dict):
            continue
        ep_no = ep.get("episodeNumber") or ep.get("episode_id") or ""
        prompts = ep.get("scenePrompts") or ep.get("prompts") or []
        if not isinstance(prompts, list):
            continue
        items = []
        for index, prompt in enumerate(prompts[:30]):
            if isinstance(prompt, str):
                items.append({"title": f"场景 {index + 1}", "subtitle": "", "body": prompt[:600]})
            elif isinstance(prompt, dict):
                scene = prompt.get("scene_id") or prompt.get("sceneId") or index + 1
                text = prompt.get("prompt") or prompt.get("content") or ""
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
    "relationship_network_cards",
    "storyboard_to_cards",
    "episode_outline_cards",
    "format_detail_list",
    "compliance_passed",
]
