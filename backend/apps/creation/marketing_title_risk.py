# -*- coding: utf-8 -*-
"""title-risk-review：剧名低俗/风险关键词快检。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

_RISK_WORDS = (
    "淫秽",
    "色情",
    "赌博",
    "毒品",
    "法轮功",
    "台独",
    "裸聊",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def review_title_risk(title: str) -> Dict[str, object]:
    t = (title or "").strip()
    hits: List[str] = []
    lower = t.lower()
    for word in _RISK_WORDS:
        if word in t or word.lower() in lower:
            hits.append(word)
    return {
        "passed": len(hits) == 0,
        "checkedAt": _now_iso(),
        "title": t,
        "hits": hits,
        "issues": [f"剧名含风险词：{w}" for w in hits],
    }
