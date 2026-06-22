# -*- coding: utf-8
"""从 dict 列表提取卡片展示字段。"""
from __future__ import annotations

from typing import Any, Dict, List

from apps.drama.presentation.text_localize import localize_display_text, sanitize_display_string
from apps.drama.presentation.labels import FIELD_LABELS

TITLE_KEYS = (
    "competitor_name",
    "name",
    "title",
    "label",
    "character",
    "role_name",
    "episodeNumber",
    "episode_no",
    "episode_id",
    "space_name",
    "target_episode",
    "dimension",
    "hook_id",
    "card_position",
    "source_id",
    "镜号",
    "场景",
)

SUBTITLE_KEYS = (
    "core_score",
    "score",
    "rating",
    "episode_count",
    "grade",
    "level",
    "status",
    "type",
)

BODY_KEYS = (
    "defect",
    "summary",
    "description",
    "detail",
    "content",
    "body",
    "analysis",
    "insert_event",
    "optimization",
    "cliffhanger",
    "hook_opening",
    "hook_content",
    "core_conflict",
    "vertical_show_feature",
    "flaw",
    "ghost",
    "lie",
    "identity",
    "want",
    "need",
    "surface_want",
    "deep_need",
    "interaction_rule",
    "core_logic",
    "update_content",
    "叙事目的",
    "画面内容(△开头)",
    "画面内容",
    "character_arc",
    "hook_calculation",
)


def dicts_to_cards(items: List[dict], *, limit: int = 20) -> List[Dict[str, str]]:
    cards: List[Dict[str, str]] = []
    for index, item in enumerate(items[:limit]):
        if not isinstance(item, dict):
            continue
        title = ""
        for key in TITLE_KEYS:
            if item.get(key) not in (None, ""):
                title = str(item[key])
                break
        if not title:
            title = f"条目 {index + 1}"

        subtitle_parts = []
        for key in SUBTITLE_KEYS:
            if item.get(key) not in (None, ""):
                label = FIELD_LABELS.get(key) or key
                subtitle_parts.append(f"{label} {item[key]}")
        subtitle = " · ".join(subtitle_parts[:3])

        body_parts = []
        for key in BODY_KEYS:
            val = item.get(key)
            if isinstance(val, str) and val.strip():
                body_parts.append(val.strip())
        body = "\n".join(body_parts)[:600]

        cards.append(
            {
                "title": sanitize_display_string(localize_display_text(title)),
                "subtitle": sanitize_display_string(localize_display_text(subtitle)),
                "body": sanitize_display_string(localize_display_text(body)),
            }
        )
    return cards
