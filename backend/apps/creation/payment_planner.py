# -*- coding: utf-8 -*-
"""payment-planner：付费卡点排期（规则层，并入 creativePlan）。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


_PAYWALL_MARKER_LABELS = {
    "paywall": "付费卡点",
    "strong-hook": "强钩子",
    "cliffhanger": "悬念卡点",
}


def _checkpoint(ep: int, marker: str, *, description: str = "") -> dict:
    return {
        "episode": ep,
        "marker": marker,
        "markerLabel": _PAYWALL_MARKER_LABELS.get(marker, marker),
        "description": description or f"第{ep}集{_PAYWALL_MARKER_LABELS.get(marker, marker)}",
    }


def build_payment_checkpoints(
    total_episodes: int,
    *,
    structure_plan: Optional[dict] = None,
) -> List[dict]:
    total = max(1, int(total_episodes or 80))
    points: List[dict] = []
    seen: set[int] = set()

    def add(ep: int, marker: str, desc: str = "") -> None:
        if 1 <= ep <= total and ep not in seen:
            points.append(_checkpoint(ep, marker, description=desc))
            seen.add(ep)

    if total >= 30:
        for ep in (8, 9, 10):
            add(ep, "paywall")
    if total >= 50:
        for ep in (20, 30):
            add(ep, "strong-hook", f"第{ep}集强钩子/中段付费牵引")
    if total >= 70:
        for ep in (40, 50):
            add(ep, "cliffhanger", f"第{ep}集悬念卡点")
    if total >= 80:
        add(60, "paywall", "第60集大段付费门槛")

    structure = structure_plan if isinstance(structure_plan, dict) else {}
    for rev in structure.get("keyReversalPoints") or []:
        if not isinstance(rev, dict):
            continue
        ep = rev.get("episodeNumber")
        if ep is None:
            continue
        ep = int(ep)
        if ep not in seen and 1 <= ep <= total:
            add(ep, "strong-hook", (rev.get("description") or "")[:80] or f"第{ep}集反转付费点")

    return sorted(points, key=lambda p: int(p.get("episode") or 0))[:16]


def merge_payment_into_creative_plan(
    creative_plan: dict,
    *,
    total_episodes: int = 80,
    structure_plan: Optional[dict] = None,
) -> dict:
    out = dict(creative_plan or {})
    existing = out.get("paymentCheckpoints") or []
    if isinstance(existing, list) and existing:
        return out
    out["paymentCheckpoints"] = build_payment_checkpoints(
        total_episodes,
        structure_plan=structure_plan,
    )
    return out
