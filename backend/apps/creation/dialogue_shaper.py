# -*- coding: utf-8 -*-
"""dialogue-shaper：竖屏短句台词规范（规则层，非 LLM）。"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .artifact_renderer import episode_to_gate_markdown

MAX_DIALOGUE_CHARS = 40
_STRIP_PUNCT_TAIL = re.compile(r"[，。！？、；：…]+$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def line_char_count(text: str) -> int:
    """不计空白的对白字数。"""
    return len(re.sub(r"\s+", "", text or ""))


def truncate_dialogue_line(line: str, *, max_chars: int = MAX_DIALOGUE_CHARS) -> Tuple[str, bool]:
    raw = (line or "").strip()
    if not raw:
        return "", False
    if line_char_count(raw) <= max_chars:
        return raw, False
    buf: List[str] = []
    count = 0
    for ch in raw:
        if ch.isspace():
            continue
        if count >= max_chars - 1:
            break
        buf.append(ch)
        count += 1
    trimmed = "".join(buf).rstrip("，。！？、；：…")
    return f"{trimmed}…", True


def build_character_maps(characters: dict) -> Tuple[Dict[str, str], Dict[str, str]]:
    id_to_name: Dict[str, str] = {}
    name_to_id: Dict[str, str] = {}
    if not isinstance(characters, dict):
        return id_to_name, name_to_id

    pools = list(characters.get("characters") or [])
    for key in ("protagonists", "antagonists", "supportingRoles"):
        pools.extend(characters.get(key) or [])

    for c in pools:
        if not isinstance(c, dict):
            continue
        cid = (c.get("id") or c.get("characterId") or "").strip()
        name = (c.get("name") or "").strip()
        if cid and name:
            id_to_name[cid] = name
            name_to_id[name] = cid
    return id_to_name, name_to_id


def _normalize_speaker(
    speaker: str,
    *,
    id_to_name: Dict[str, str],
    name_to_id: Dict[str, str],
) -> Tuple[str, str]:
    sp = (speaker or "").strip() or "角色"
    if sp in id_to_name:
        return id_to_name[sp], sp
    if sp in name_to_id:
        return sp, name_to_id[sp]
    return sp, ""


def shape_scene_dialogues(
    scene: dict,
    *,
    id_to_name: Dict[str, str],
    name_to_id: Dict[str, str],
) -> int:
    if not isinstance(scene, dict):
        return 0
    truncated = 0
    dialogues = scene.get("dialogues") or []
    if not isinstance(dialogues, list):
        return 0

    shaped: List[dict] = []
    for idx, dlg in enumerate(dialogues):
        if not isinstance(dlg, dict):
            continue
        speaker_raw = dlg.get("speaker") or dlg.get("character") or "角色"
        display_name, speaker_id = _normalize_speaker(
            str(speaker_raw),
            id_to_name=id_to_name,
            name_to_id=name_to_id,
        )
        line, was_cut = truncate_dialogue_line(str(dlg.get("line") or ""))
        if was_cut:
            truncated += 1
        row = dict(dlg)
        row["speaker"] = display_name
        if speaker_id:
            row["speakerId"] = speaker_id
        row["line"] = line
        row["order"] = int(dlg.get("order") or idx + 1)
        row["charCount"] = line_char_count(line)
        shaped.append(row)
    scene["dialogues"] = shaped
    return truncated


def shape_episode_dialogues(
    episode: dict,
    *,
    id_to_name: Dict[str, str],
    name_to_id: Dict[str, str],
) -> int:
    if not isinstance(episode, dict):
        return 0
    total = 0
    for scene in episode.get("scenes") or []:
        total += shape_scene_dialogues(
            scene,
            id_to_name=id_to_name,
            name_to_id=name_to_id,
        )
    if total or episode.get("scenes"):
        episode["scriptMarkdown"] = episode_to_gate_markdown(episode)
    return total


def apply_dialogue_shaper(
    payload: dict,
    characters: dict,
    *,
    max_chars: int = MAX_DIALOGUE_CHARS,
) -> Tuple[dict, dict]:
    """规范化 episodes 内台词并刷新 scriptMarkdown。"""
    if not isinstance(payload, dict):
        return payload, {"passed": True, "skipped": True, "issues": []}

    episodes = payload.get("episodes") or []
    if not episodes:
        return payload, {
            "passed": True,
            "skipped": True,
            "reason": "无剧集",
            "checkedAt": _now_iso(),
            "issues": [],
        }

    id_to_name, name_to_id = build_character_maps(characters)
    total_truncated = 0
    long_before = 0

    for ep in episodes:
        if not isinstance(ep, dict):
            continue
        for scene in ep.get("scenes") or []:
            if not isinstance(scene, dict):
                continue
            for dlg in scene.get("dialogues") or []:
                if isinstance(dlg, dict) and line_char_count(str(dlg.get("line") or "")) > max_chars:
                    long_before += 1
        total_truncated += shape_episode_dialogues(
            ep,
            id_to_name=id_to_name,
            name_to_id=name_to_id,
        )

    issues: List[str] = []
    if total_truncated:
        issues.append(f"已截断 {total_truncated} 条超长台词（>{max_chars} 字）")

    log = {
        "passed": True,
        "checkedAt": _now_iso(),
        "maxChars": max_chars,
        "truncatedCount": total_truncated,
        "longLinesBefore": long_before,
        "issues": issues,
    }
    return payload, log
