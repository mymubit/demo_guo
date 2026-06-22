# -*- coding: utf-8 -*-
"""Project.agent_notes 规范化（skill-agent/32）。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

AGENT_NOTES_LIST_LIMIT = 20
AGENT_NOTES_STRING_LIMIT = 2000


def _trim_list(values: Any, *, limit: int = AGENT_NOTES_LIST_LIMIT) -> List[str]:
    if not isinstance(values, list):
        return []
    cleaned = [str(v).strip() for v in values if str(v).strip()]
    return cleaned[-limit:]


def normalize_agent_notes(raw: Dict[str, Any] | None) -> Dict[str, Any]:
    notes = dict(raw or {})
    merged: Dict[str, Any] = {
        "rejects": _trim_list(notes.get("rejects")),
        "style_preferences": _trim_list(notes.get("style_preferences")),
        "character_guidance": str(notes.get("character_guidance") or "")[:AGENT_NOTES_STRING_LIMIT],
    }
    if notes.get("last_feedback_at"):
        merged["last_feedback_at"] = str(notes["last_feedback_at"])
    return merged


def merge_agent_notes_patch(existing: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    merged = normalize_agent_notes(existing)
    for key in ("rejects", "style_preferences", "character_guidance"):
        if key in patch:
            if key == "character_guidance":
                merged[key] = str(patch[key] or "")[:AGENT_NOTES_STRING_LIMIT]
            else:
                merged[key] = _trim_list(patch[key])
    merged["last_feedback_at"] = datetime.now(timezone.utc).isoformat()
    return merged
