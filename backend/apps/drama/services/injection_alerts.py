# -*- coding: utf-8 -*-
"""注入告警：读详情时按 InjectionManifest 计算，不落库。"""
from __future__ import annotations

from typing import Any

from django.conf import settings


ALERT_SYSTEM_CHARS_HIGH = "system_chars_high"
ALERT_LAYER_DOMINANT = "layer_dominant"
ALERT_BUDGET_TRUNCATED = "budget_truncated"
ALERT_ENABLE_SKIPPED_CORE = "enable_skipped_core"
ALERT_BUNDLE_VERSION_DRIFT = "bundle_version_drift"

_LEVEL_WARN = "warn"
_LEVEL_INFO = "info"


def _abs_system_chars_cap(agent_id: str = "") -> int:
    overrides = getattr(settings, "INJECTION_ALERT_SYSTEM_CHARS_BY_ROLE", None) or {}
    if isinstance(overrides, dict) and agent_id and agent_id in overrides:
        try:
            return int(overrides[agent_id])
        except (TypeError, ValueError):
            pass
    return int(getattr(settings, "INJECTION_ALERT_SYSTEM_CHARS_ABS", 100_000) or 100_000)


def _layer_dominant_ratio() -> float:
    try:
        return float(getattr(settings, "INJECTION_ALERT_LAYER_DOMINANT_RATIO", 0.45) or 0.45)
    except (TypeError, ValueError):
        return 0.45


def _manifest_any_truncated(manifest: dict[str, Any]) -> bool:
    layers = manifest.get("layers") or {}
    if isinstance(layers, dict):
        for stat in layers.values():
            if isinstance(stat, dict) and stat.get("truncated"):
                return True
    rules = manifest.get("rules") or {}
    if isinstance(rules, dict) and rules.get("truncated"):
        return True
    knowledge = manifest.get("knowledge") or {}
    if isinstance(knowledge, dict) and knowledge.get("truncated"):
        return True
    modules = manifest.get("modules") or {}
    if isinstance(modules, dict) and modules.get("truncated"):
        return True
    return False


def _core_module_ids_from_catalog() -> frozenset[str]:
    try:
        from apps.drama.services.skills_loader import get_skills_loader

        catalog = get_skills_loader().modules_catalog.get("modules") or {}
    except Exception:
        return frozenset()
    ids: set[str] = set()
    for mid, meta in catalog.items():
        if isinstance(meta, dict) and str(meta.get("kind") or "") == "core":
            ids.add(str(mid))
    return frozenset(ids)


def compute_injection_alerts(
    manifest: dict[str, Any] | None,
    *,
    call_status: str = "",
    core_module_ids: frozenset[str] | None = None,
    current_bundle_version: str | None = None,
) -> list[dict[str, Any]]:
    """按 spec §7.2 计算告警列表；manifest 为空返回 []。"""
    if not isinstance(manifest, dict):
        return []

    alerts: list[dict[str, Any]] = []
    agent_id = str(manifest.get("agent_id") or "")
    system_chars = int(manifest.get("system_chars") or 0)
    cap = _abs_system_chars_cap(agent_id)
    if system_chars > cap:
        alerts.append(
            {
                "id": ALERT_SYSTEM_CHARS_HIGH,
                "level": _LEVEL_WARN,
                "message": f"system_chars={system_chars} 超过绝对上限 {cap}",
                "detail": {"system_chars": system_chars, "cap": cap},
            }
        )

    layers = manifest.get("layers") or {}
    ratio_cap = _layer_dominant_ratio()
    if isinstance(layers, dict) and system_chars > 0:
        from apps.drama.services.injection_manifest import normalize_layers

        for name, stat in normalize_layers(layers).items():
            if not isinstance(stat, dict):
                continue
            chars = int(stat.get("chars") or 0)
            if chars <= 0:
                continue
            ratio = chars / system_chars
            if ratio > ratio_cap:
                alerts.append(
                    {
                        "id": ALERT_LAYER_DOMINANT,
                        "level": _LEVEL_WARN,
                        "message": f"层 {name} 占比 {ratio:.0%} 超过 {ratio_cap:.0%}",
                        "detail": {
                            "layer": name,
                            "chars": chars,
                            "ratio": round(ratio, 4),
                            "threshold": ratio_cap,
                        },
                    }
                )

    if _manifest_any_truncated(manifest):
        alerts.append(
            {
                "id": ALERT_BUDGET_TRUNCATED,
                "level": _LEVEL_WARN,
                "message": "注入预算发生截断",
                "detail": {},
            }
        )

    live_bundle = str(manifest.get("bundle_version") or "").strip()
    current = (current_bundle_version or "").strip()
    if not current:
        try:
            from apps.drama.services.skills_loader import get_skills_loader

            current = str(getattr(get_skills_loader(), "bundle_version", "") or "").strip()
        except Exception:
            current = ""
    if live_bundle and current and live_bundle != current:
        alerts.append(
            {
                "id": ALERT_BUNDLE_VERSION_DRIFT,
                "level": _LEVEL_WARN,
                "message": (
                    f"技能包版本漂移：调用时 {live_bundle} ≠ 当前 {current}；"
                    "不可用作改前/改后对照基线"
                ),
                "detail": {
                    "manifest_bundle_version": live_bundle,
                    "current_bundle_version": current,
                },
            }
        )

    status = (call_status or "").lower()
    failed = status in {"error", "failed", "timeout"}
    if failed:
        cores = core_module_ids if core_module_ids is not None else _core_module_ids_from_catalog()
        skipped = (manifest.get("modules") or {}).get("skipped") or []
        core_skipped = [
            m
            for m in skipped
            if isinstance(m, dict) and str(m.get("id") or "") in cores
        ]
        if core_skipped:
            ids = [str(m.get("id")) for m in core_skipped]
            alerts.append(
                {
                    "id": ALERT_ENABLE_SKIPPED_CORE,
                    "level": _LEVEL_INFO,
                    "message": f"失败调用跳过了 core 模块: {', '.join(ids)}",
                    "detail": {"module_ids": ids},
                }
            )

    return alerts


def highest_alert_level(alerts: list[dict[str, Any]]) -> str | None:
    if not alerts:
        return None
    if any(a.get("level") == _LEVEL_WARN for a in alerts):
        return _LEVEL_WARN
    if any(a.get("level") == _LEVEL_INFO for a in alerts):
        return _LEVEL_INFO
    return None
