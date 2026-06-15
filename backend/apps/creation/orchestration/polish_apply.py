# -*- coding: utf-8 -*-
"""PolishAgent：将润色建议写回剧本产物（用户确认后）。"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from django.utils import timezone

from ..artifact_service import get_artifact, save_artifact
from ..models import Project

logger = logging.getLogger(__name__)


def _normalize_suggestion(raw: Any, index: int) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {"index": index, "text": str(raw), "field": "notes", "episodeNumber": None}
    ep = raw.get("episodeNumber") or raw.get("episode")
    return {
        "index": index,
        "episodeNumber": int(ep) if ep is not None else None,
        "field": (raw.get("field") or raw.get("action") or "notes").strip(),
        "advice": (raw.get("advice") or raw.get("text") or "").strip(),
        "type": raw.get("type") or "",
    }


def apply_polish_suggestions(
    project: Project,
    *,
    indices: Optional[List[int]] = None,
    apply_all: bool = False,
    patch_script_fields: bool = False,
) -> Dict[str, Any]:
    """将 polish_log 中的建议写入 episode_scripts（默认写 polishRevisionNotes）。"""
    polish_log = get_artifact(project, "polish_log") or {}
    suggestions_in = polish_log.get("suggestions") or []
    if not suggestions_in:
        raise ValueError("暂无润色建议可应用")

    normalized = [_normalize_suggestion(s, i) for i, s in enumerate(suggestions_in)]
    if apply_all:
        selected: Set[int] = {n["index"] for n in normalized}
    elif indices is not None:
        selected = {int(i) for i in indices}
    else:
        selected = {n["index"] for n in normalized if n.get("advice")}

    if not selected:
        raise ValueError("未选择任何润色建议")

    scripts = get_artifact(project, "episode_scripts") or {}
    episodes = list(scripts.get("episodes") or [])
    by_num = {
        int(e["episodeNumber"]): e for e in episodes if isinstance(e, dict) and e.get("episodeNumber")
    }

    applied_records: List[Dict[str, Any]] = []
    now = timezone.now().isoformat()

    for item in normalized:
        if item["index"] not in selected:
            continue
        advice = item["advice"]
        if not advice:
            continue

        record = {
            "index": item["index"],
            "episodeNumber": item["episodeNumber"],
            "field": item["field"],
            "advice": advice[:2000],
        }
        ep_num = item["episodeNumber"]
        if ep_num and ep_num in by_num:
            ep = by_num[ep_num]
            notes = list(ep.get("polishRevisionNotes") or [])
            notes.append(
                {
                    "advice": advice[:2000],
                    "field": item["field"],
                    "type": item["type"],
                    "appliedAt": now,
                }
            )
            ep["polishRevisionNotes"] = notes[-20:]

            if patch_script_fields and item["field"] in (
                "dialogue",
                "full_script_text",
                "scriptMarkdown",
                "script",
            ):
                for key in ("full_script_text", "scriptMarkdown"):
                    if key in ep or key == "full_script_text":
                        prev = (ep.get(key) or "").rstrip()
                        ep[key] = f"{prev}\n\n> [润色建议] {advice}\n"
                        record["patchedField"] = key
                        break
        applied_records.append(record)

    scripts["episodes"] = sorted(by_num.values(), key=lambda x: int(x["episodeNumber"]))
    save_artifact(project, "episode_scripts", scripts)

    already = set(polish_log.get("appliedIndices") or [])
    already.update(selected)
    polish_log["applied"] = True
    polish_log["appliedAt"] = now
    polish_log["appliedIndices"] = sorted(already)
    polish_log["appliedRecords"] = (polish_log.get("appliedRecords") or []) + applied_records
    polish_log["mode"] = "apply"
    save_artifact(project, "polish_log", polish_log)

    logger.info(
        "[PolishAgent] applied project=%s count=%s patch_fields=%s",
        project.id,
        len(applied_records),
        patch_script_fields,
    )
    return {
        "appliedCount": len(applied_records),
        "appliedIndices": sorted(selected),
        "patchScriptFields": patch_script_fields,
        "polish_log": polish_log,
    }
