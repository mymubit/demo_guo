# -*- coding: utf-8 -*-
"""V3 质量/合规报告元数据（正文版本溯源与过期判定）。"""
from __future__ import annotations

from typing import Any

from apps.drama.models import V3ArtifactVersion

META_KEY = "_v3_meta"


def attach_script_meta(payload: dict, *, script_art: V3ArtifactVersion) -> dict:
    """将正文版本写入 payload._v3_meta（不修改入参）。"""
    out = dict(payload)
    out[META_KEY] = {
        "source_script_version": script_art.version,
        "source_script_artifact_id": str(script_art.id),
    }
    return out


def strip_meta_for_validate(payload: dict) -> dict:
    """剥离编排器附加字段，供 schema 校验使用（不修改入参）。"""
    out = dict(payload)
    out.pop(META_KEY, None)
    return out


def read_source_script_version(payload: dict) -> int | None:
    """读取报告 payload 中的 source_script_version。"""
    meta = payload.get(META_KEY)
    if not isinstance(meta, dict):
        return None
    ver: Any = meta.get("source_script_version")
    if ver is None:
        return None
    try:
        return int(ver)
    except (TypeError, ValueError):
        return None


def is_report_stale(
    *,
    report_payload: dict,
    current_script: V3ArtifactVersion | None,
) -> bool:
    """当前 committed episode_scripts.version ≠ _v3_meta.source_script_version 则为过期。"""
    if current_script is None:
        return True
    source = read_source_script_version(report_payload)
    if source is None:
        return True
    return int(current_script.version) != source
