# -*- coding: utf-8 -*-
"""按 schema_version 将 Drama 产物转为统一 blocks 视图。"""
from __future__ import annotations

from typing import Any

from apps.drama.presentation.base import (
    build_blocks_from_value,
    label,
    normalize_payload,
    paragraph_block,
    view,
)
from apps.drama.presentation.labels import ARTIFACT_LABELS
from apps.drama.presentation.normalize import format_scalar
from apps.drama.presentation.schema_presenters import SCHEMA_PRESENTERS
from apps.drama.presentation.text_localize import sanitize_blocks, sanitize_display_string

# 按 schema_version 注册专用展示器
from apps.drama.presentation.schema_presenters import (  # noqa: F401
    present_character_bible,
    present_compliance_report,
    present_episode_scripts,
    present_market_analysis,
    present_marketing_kit,
    present_project_brief,
    present_quality_report,
    present_review_report,
    present_series_outline,
)


def present_generic(artifact_key: str, payload: Any, *, schema_version: str = "") -> dict:
    body = normalize_payload(payload)
    blocks = []
    if not isinstance(body, dict):
        text = format_scalar(body)
        if text and text != "—":
            blocks.append(paragraph_block(ARTIFACT_LABELS.get(artifact_key) or artifact_key, text))
        return view(artifact_key, schema_version or "generic.v1", blocks)

    for key, value in body.items():
        blocks.extend(build_blocks_from_value(str(key), value, depth=0))

    return view(artifact_key, schema_version or "generic.v1", blocks)


def present_artifact(artifact_key: str, schema_version: str, payload: Any) -> dict:
    if payload in (None, {}, []):
        return view(artifact_key, schema_version, [], summary="暂无内容")
    presenter = SCHEMA_PRESENTERS.get(schema_version)
    if presenter:
        result = presenter(artifact_key, payload)
    else:
        result = view(
            artifact_key,
            schema_version,
            [],
            summary=f"未注册展示器：{schema_version}",
        )
    result["blocks"] = sanitize_blocks(result.get("blocks") or [])
    if result.get("summary"):
        result["summary"] = sanitize_display_string(str(result["summary"]))[:240]
    return result
