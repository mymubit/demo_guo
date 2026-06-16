# -*- coding: utf-8 -*-
"""LLM 剧本产物归一化：补齐 scenes、商业场头，清理历史占位假数据。"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .artifact_renderer import episode_to_markdown

SCENE_HEADER_RE = re.compile(
    r"^(\d+)-(\d+)\s+(日|夜|晨|昏|黄昏|深夜)\s+(内|外)\s+(\S+)"
)
DIALOGUE_MARKDOWN_RE = re.compile(
    r"^\*\*([^*]+)\*\*(?:\s*\(([^)]*)\))?\s*[:：]\s*(.+)$"
)
DIALOGUE_PLAIN_RE = re.compile(
    r"^([\u4e00-\u9fff]{2,12})(?:（([^）]{0,24})）|\(([^)]{0,24})\))?(?:OS)?[:：]\s*(.+)$"
)
ACTION_MARKER_RE = re.compile(r"^[△^▲]\s*(.+)$")
SKIP_LINE_RE = re.compile(
    r"^(?:[IVX]+\s|【未完待续】|【完】|\[\]|[-—]{2,})$"
)
LEGACY_NUMBER_SUFFIX_RE = re.compile(r"[（(]\d+[）)]$")

LEGACY_PLACEHOLDER_DIALOGUE_HINTS = (
    "这件事还没完，我会查到底",
    "你现在必须给我一句实话",
    "这一页记录你转移资产的每一笔",
)
LEGACY_PLACEHOLDER_ACTION_HINTS = (
    "将线索逐条摊开，镜头推近，情绪持续升温",
    "目光收紧，气氛骤然压下来",
    "林晚将证据逐页摊开",
    "逼对方正视代价",
)

MAX_SCENES = 3

DEFAULT_COLOR = {
    "kelvinCode": "k5500-daylight-neutral",
    "kelvinValue": 5500,
    "mood": "中性日光",
}
DEFAULT_SOUND = {
    "category": "dialogue-dominant",
    "description": "环境底噪与人声",
    "keySoundEffects": [],
    "musicMood": "none-silence",
    "volumeHint": "medium",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _cjk_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text or ""))


def _is_legacy_placeholder_text(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return True
    core = LEGACY_NUMBER_SUFFIX_RE.sub("", raw).strip()
    for hint in LEGACY_PLACEHOLDER_DIALOGUE_HINTS + LEGACY_PLACEHOLDER_ACTION_HINTS:
        if hint in core:
            return True
    if LEGACY_NUMBER_SUFFIX_RE.search(raw) and len(core) <= 28:
        return True
    return False


def _dedupe_dialogues(dialogues: List[dict]) -> List[dict]:
    seen: set[str] = set()
    out: List[dict] = []
    for dlg in dialogues:
        if not isinstance(dlg, dict):
            continue
        line = (dlg.get("line") or "").strip()
        speaker = (dlg.get("speaker") or "").strip()
        if not line or _is_legacy_placeholder_text(line):
            continue
        key = f"{speaker}:{line}"
        if key in seen:
            continue
        seen.add(key)
        row = dict(dlg)
        row["order"] = len(out) + 1
        out.append(row)
    return out


def _dedupe_actions(actions: List[dict]) -> List[dict]:
    seen: set[str] = set()
    out: List[dict] = []
    for act in actions:
        if isinstance(act, dict):
            content = (act.get("content") or "").strip()
        else:
            content = str(act or "").strip()
        if not content:
            continue
        content = re.sub(r"^△\s*", "", content).strip()
        if _is_legacy_placeholder_text(content):
            continue
        if content in seen:
            continue
        seen.add(content)
        row = act if isinstance(act, dict) else {"content": content}
        row = dict(row)
        row["order"] = len(out) + 1
        row["content"] = content[:500]
        out.append(row)
    return out


def _sanitize_scenes(scenes: List[dict]) -> List[dict]:
    cleaned: List[dict] = []
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        row = dict(scene)
        row["actions"] = _dedupe_actions(row.get("actions") or [])
        row["dialogues"] = _dedupe_dialogues(row.get("dialogues") or [])
        if row["actions"] or row["dialogues"]:
            cleaned.append(row)
    return cleaned


def _parse_scene_header(line: str, default_ep: int) -> Optional[dict]:
    text = (line or "").strip()
    if text.startswith("###"):
        text = text.lstrip("#").strip()
    match = SCENE_HEADER_RE.match(text)
    if match:
        ep_num, scene_idx, tod, ie, loc = match.groups()
        tod = "夜" if tod in ("深夜",) else ("日" if tod == "黄昏" else tod)
        return {
            "sceneNumber": f"{ep_num}-{scene_idx}",
            "timeOfDay": tod,
            "interiorExterior": ie,
            "location": loc,
        }
    loose = re.match(r"^(\d+)-(\d+)\s+(.+)$", text)
    if loose:
        ep_num, scene_idx, rest = loose.groups()
        tod = "日"
        ie = "内"
        loc = rest.strip() or "主场景"
        if "夜" in rest:
            tod = "夜"
        if "外" in rest and "内" not in rest[:2]:
            ie = "外"
        loc = re.sub(r"(日|夜|晨|昏|内|外)\s*", "", loc).strip() or "主场景"
        return {
            "sceneNumber": f"{ep_num}-{scene_idx}",
            "timeOfDay": tod,
            "interiorExterior": ie,
            "location": loc[:28],
        }
    return None


def _build_scene(
    ep_num: int,
    scene_idx: int,
    *,
    time_of_day: str = "日",
    interior_exterior: str = "内",
    location: str = "主场景",
) -> dict:
    loc = (location or "主场景").strip()[:28] or "主场景"
    tod = time_of_day if time_of_day in ("日", "夜", "晨", "黄昏", "深夜") else "日"
    ie = interior_exterior if interior_exterior in ("内", "外", "内外") else "内"
    scene_number = f"{ep_num}-{scene_idx}"
    heading = f"{scene_number} {tod} {ie} {loc}"
    return {
        "sceneHeading": heading,
        "sceneNumber": scene_number,
        "timeOfDay": tod,
        "interiorExterior": ie,
        "location": loc,
        "colorTemperature": dict(DEFAULT_COLOR),
        "soundDesign": dict(DEFAULT_SOUND),
        "actions": [],
        "dialogues": [],
    }


def _normalize_scene_fields(scene: dict, ep_num: int, scene_idx: int) -> dict:
    row = dict(scene or {})
    header = _parse_scene_header(row.get("sceneHeading") or "", ep_num)
    if not header and row.get("sceneNumber"):
        header = _parse_scene_header(str(row.get("sceneNumber")), ep_num)
    if header:
        row.update(header)
    if not row.get("sceneNumber"):
        row["sceneNumber"] = f"{ep_num}-{scene_idx}"
    if not row.get("location"):
        row["location"] = "主场景"
    if not row.get("timeOfDay"):
        row["timeOfDay"] = "日"
    if not row.get("interiorExterior"):
        row["interiorExterior"] = "内"
    row["sceneHeading"] = (
        f"{row['sceneNumber']} {row['timeOfDay']} {row['interiorExterior']} {row['location']}"
    )
    row.setdefault("colorTemperature", dict(DEFAULT_COLOR))
    row.setdefault("soundDesign", dict(DEFAULT_SOUND))
    row["actions"] = _dedupe_actions(row.get("actions") or [])
    row["dialogues"] = _dedupe_dialogues(row.get("dialogues") or [])
    return row


def _append_action(scene: dict, content: str) -> None:
    text = re.sub(r"^△\s*", "", (content or "").strip())
    if not text or not re.search(r"[\u4e00-\u9fff]", text) or _is_legacy_placeholder_text(text):
        return
    actions = scene.setdefault("actions", [])
    key = text
    if any((a.get("content") or "") == key for a in actions if isinstance(a, dict)):
        return
    actions.append({"order": len(actions) + 1, "content": text[:500]})


def _append_dialogue(scene: dict, speaker: str, line: str, action_note: str = "") -> None:
    sp = (speaker or "角色").strip() or "角色"
    text = (line or "").strip()
    if not text or _is_legacy_placeholder_text(text):
        return
    dialogues = scene.setdefault("dialogues", [])
    key = f"{sp}:{text}"
    if any(f"{d.get('speaker')}:{d.get('line')}" == key for d in dialogues if isinstance(d, dict)):
        return
    row: dict = {
        "order": len(dialogues) + 1,
        "speaker": sp[:12],
        "line": text[:200],
    }
    if action_note:
        row["actionNote"] = action_note[:24]
    dialogues.append(row)


def _parse_dialogue_line(line: str) -> Optional[Tuple[str, str, str]]:
    text = (line or "").strip()
    if not text:
        return None
    match = DIALOGUE_MARKDOWN_RE.match(text)
    if match:
        return match.group(1).strip(), match.group(3).strip(), (match.group(2) or "").strip()
    match = DIALOGUE_PLAIN_RE.match(text)
    if match:
        action = (match.group(2) or match.group(3) or "").strip()
        return match.group(1).strip(), match.group(4).strip(), action
    return None


def _parse_action_line(line: str) -> Optional[str]:
    text = (line or "").strip()
    if not text:
        return None
    match = ACTION_MARKER_RE.match(text)
    if match:
        return match.group(1).strip()
    if text.startswith("^"):
        return text.lstrip("^").strip()
    if text.startswith("**(") and text.endswith(")**"):
        return text[3:-3].strip()
    if DIALOGUE_PLAIN_RE.match(text) or DIALOGUE_MARKDOWN_RE.match(text):
        return None
    if SCENE_HEADER_RE.match(text):
        return None
    if re.search(r"[\u4e00-\u9fff]", text) and len(text) >= 4:
        return text
    return None


def parse_script_markdown_to_scenes(markdown: str, ep_num: int) -> List[dict]:
    """将自由 Markdown 解析为结构化 scenes（过滤历史占位与重复行）。"""
    scenes: List[dict] = []
    current: Optional[dict] = None
    scene_idx = 0

    for raw_line in (markdown or "").replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("#") or SKIP_LINE_RE.match(line):
            continue

        header = _parse_scene_header(line, ep_num)
        if header:
            scene_idx += 1
            current = _build_scene(
                ep_num,
                scene_idx,
                time_of_day=header["timeOfDay"],
                interior_exterior=header["interiorExterior"],
                location=header["location"],
            )
            current["sceneNumber"] = header["sceneNumber"]
            current["sceneHeading"] = (
                f"{header['sceneNumber']} {header['timeOfDay']} "
                f"{header['interiorExterior']} {header['location']}"
            )
            scenes.append(current)
            continue

        if not current:
            scene_idx += 1
            current = _build_scene(ep_num, scene_idx)
            scenes.append(current)

        dialogue = _parse_dialogue_line(line)
        if dialogue:
            speaker, line_text, action_note = dialogue
            _append_dialogue(current, speaker, line_text, action_note)
            continue

        action = _parse_action_line(line)
        if action:
            _append_action(current, action)

    return _sanitize_scenes(scenes)[:MAX_SCENES]


def normalize_episode(ep: dict, *, format_variant: str = "variant-b") -> dict:
    if not isinstance(ep, dict):
        return ep
    row = dict(ep)
    ep_num = int(row.get("episodeNumber") or 1)
    scenes = row.get("scenes") or []

    normalized_scenes: List[dict] = []
    if isinstance(scenes, list) and scenes:
        for idx, scene in enumerate(scenes[:MAX_SCENES], start=1):
            if isinstance(scene, dict):
                normalized_scenes.append(_normalize_scene_fields(scene, ep_num, idx))
    elif (row.get("scriptMarkdown") or row.get("full_script_text") or "").strip():
        md = (row.get("scriptMarkdown") or row.get("full_script_text") or "").strip()
        normalized_scenes = parse_script_markdown_to_scenes(md, ep_num)

    normalized_scenes = _sanitize_scenes(normalized_scenes)
    if not normalized_scenes:
        normalized_scenes = [_build_scene(ep_num, 1)]

    row["scenes"] = normalized_scenes[:MAX_SCENES]
    row.setdefault("durationMinutes", 2)
    row["formatVariant"] = format_variant
    row["scriptMarkdown"] = episode_to_markdown(row)
    row["wordCount"] = _cjk_len(row["scriptMarkdown"])
    row["sceneCount"] = len(row["scenes"])
    return row


def apply_script_normalizer(
    payload: dict,
    brief: Optional[dict] = None,
    *,
    characters: Optional[dict] = None,
) -> Tuple[dict, dict]:
    """批量归一化 episodes，返回 (payload, log)。"""
    del characters
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

    variant = (brief or {}).get("formatVariant") or payload.get("formatVariant") or "variant-b"
    fixed = 0
    rebuilt = 0
    stripped = 0
    out_eps: List[dict] = []

    for ep in episodes:
        if not isinstance(ep, dict):
            continue
        before_md = (ep.get("scriptMarkdown") or "").strip()
        before_scenes = len(ep.get("scenes") or [])
        normalized = normalize_episode(ep, format_variant=variant)
        after_md = (normalized.get("scriptMarkdown") or "").strip()
        after_scenes = len(normalized.get("scenes") or [])
        if before_scenes == 0 and after_scenes > 0:
            rebuilt += 1
        elif before_md and len(after_md) < len(before_md) * 0.7:
            stripped += 1
        elif before_scenes != after_scenes or after_md != before_md:
            fixed += 1
        out_eps.append(normalized)

    payload = {**payload, "episodes": out_eps}
    issues: List[str] = []
    if stripped:
        issues.append(f"已清理 {stripped} 集历史占位/重复对白")
    if rebuilt:
        issues.append(f"已从 Markdown 重建 {rebuilt} 集 scenes 结构")
    if fixed:
        issues.append(f"已修正 {fixed} 集场头/对白格式")

    return payload, {
        "passed": True,
        "checkedAt": _now_iso(),
        "rebuiltCount": rebuilt,
        "fixedCount": fixed,
        "strippedCount": stripped,
        "issues": issues,
    }
