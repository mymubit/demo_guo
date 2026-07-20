# -*- coding: utf-8 -*-
"""InjectionManifest：prompt 装配层结构化清单（与 system 正文对账）。"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


MANIFEST_VERSION = 1
# 层 chars 不含各 ## 分区标题与空行胶水；仅作占比参考，对账放宽
LAYER_RECONCILE_TOLERANCE = 512


def layer_stat(chars: int, *, truncated: bool = False) -> dict[str, Any]:
    return {"chars": int(chars), "truncated": bool(truncated)}


def build_injection_manifest(
    *,
    agent_id: str,
    bundle_version: str,
    system_prompt: str,
    user_prompt: str,
    layers: dict[str, dict[str, Any]],
    modules: dict[str, Any],
    knowledge: dict[str, Any],
    rules: dict[str, Any],
    policies: dict[str, Any],
) -> dict[str, Any]:
    """组装可落库的 InjectionManifest（version=1）。"""
    checksum = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()[:16]
    return {
        "version": MANIFEST_VERSION,
        "agent_id": agent_id,
        "bundle_version": str(bundle_version),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "layers": layers,
        "modules": modules,
        "knowledge": knowledge,
        "rules": rules,
        "policies": policies,
        "system_chars": len(system_prompt),
        "user_chars": len(user_prompt),
        "checksum": checksum,
    }


def layer_chars_sum(layers: dict[str, dict[str, Any]]) -> int:
    total = 0
    for value in layers.values():
        if isinstance(value, dict):
            total += int(value.get("chars") or 0)
    return total


def reconcile_ok(manifest: dict[str, Any], *, tolerance: int = LAYER_RECONCILE_TOLERANCE) -> bool:
    """层 chars 之和与 system_chars 是否在容差内（标题/换行导致差额）。"""
    system_chars = int(manifest.get("system_chars") or 0)
    layers = manifest.get("layers") or {}
    if not isinstance(layers, dict):
        return False
    return abs(layer_chars_sum(layers) - system_chars) <= tolerance
