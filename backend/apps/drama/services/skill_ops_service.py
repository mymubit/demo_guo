# -*- coding: utf-8 -*-
"""技能运维：只收集「能用来改技能」的结构化失败，过滤超时/连通噪音。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.drama.models import DramaLlmCallLog
from apps.drama.services.injection_alerts import compute_injection_alerts
from apps.drama.services.llm_call_log_service import _manifest_any_truncated

# 基础设施噪音：对写 anti-examples 无帮助
_INFRA_PATTERNS = (
    re.compile(r"timed?\s*out", re.I),
    re.compile(r"Read timed out", re.I),
    re.compile(r"ConnectionPool", re.I),
    re.compile(r"ConnectTimeout", re.I),
    re.compile(r"Name or service not known", re.I),
)

# 模型配置问题：应去「模型管理」改，不是改 skill
_PROVIDER_PATTERNS = (
    re.compile(r"response_format", re.I),
    re.compile(r"json_object.*not supported", re.I),
    re.compile(r"InvalidParameter", re.I),
)

_SCHEMA_ERR = re.compile(r"Schema|不是合法 JSON|JSON 对象|产物 Schema", re.I)

CAUSE_SCHEMA = "schema_contract"
CAUSE_OVER_INJECTION = "over_injection"
CAUSE_MISSING_MODULE = "missing_module"
CAUSE_MODEL_ERROR = "model_error"
CAUSE_UNKNOWN = "unknown"


def _skills_root() -> Path:
    return Path(settings.DRAMA_SKILLS_ROOT)


def _classify(log: DramaLlmCallLog) -> str | None:
    """返回 skill_structure | provider_config | infra | None(忽略)。"""
    purpose = log.purpose or ""
    err = log.error_message or ""
    role = log.role or ""

    if purpose == "connectivity_test" or role.startswith("admin."):
        return "infra"
    for pat in _INFRA_PATTERNS:
        if pat.search(err):
            return "infra"
    for pat in _PROVIDER_PATTERNS:
        if pat.search(err):
            return "provider_config"

    if "json_repair" in purpose:
        return "skill_structure"
    if _SCHEMA_ERR.search(err):
        return "skill_structure"
    # 生成类错误但无明确结构信息：不进技能运维主列表
    return None


def _core_ids_from_manifest_skipped(manifest: dict[str, Any] | None) -> list[str]:
    if not isinstance(manifest, dict):
        return []
    try:
        from apps.drama.services.skills_loader import get_skills_loader

        catalog = get_skills_loader().modules_catalog.get("modules") or {}
    except Exception:
        catalog = {}
    cores = {
        str(mid)
        for mid, meta in catalog.items()
        if isinstance(meta, dict) and str(meta.get("kind") or "") == "core"
    }
    skipped = (manifest.get("modules") or {}).get("skipped") or []
    return [
        str(m.get("id"))
        for m in skipped
        if isinstance(m, dict) and str(m.get("id") or "") in cores
    ]


def infer_suspected_causes(log: DramaLlmCallLog, category: str) -> list[str]:
    """spec §7.3 失败归因启发式。"""
    if category in {"infra", "provider_config"}:
        return [CAUSE_MODEL_ERROR]

    err = log.error_message or ""
    status = (log.status or "").lower()
    response = (log.response_text or "").strip()
    manifest = log.injection_manifest if isinstance(log.injection_manifest, dict) else None
    truncated = bool(_manifest_any_truncated(manifest))
    schema_fail = bool(_SCHEMA_ERR.search(err) or "json_repair" in (log.purpose or ""))

    causes: list[str] = []
    if status in {"error", "failed", "timeout"} and not response and not schema_fail:
        causes.append(CAUSE_MODEL_ERROR)

    if schema_fail or category == "skill_structure":
        causes.append(CAUSE_SCHEMA)
        if truncated:
            causes.append(CAUSE_OVER_INJECTION)

    if status in {"error", "failed"} and _core_ids_from_manifest_skipped(manifest):
        causes.append(CAUSE_MISSING_MODULE)

    # 去重保序
    seen: set[str] = set()
    ordered: list[str] = []
    for c in causes:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return ordered or [CAUSE_UNKNOWN]


def _injection_summary(log: DramaLlmCallLog) -> dict[str, Any] | None:
    manifest = log.injection_manifest if isinstance(log.injection_manifest, dict) else None
    if not manifest:
        return None
    modules = manifest.get("modules") or {}
    alerts = compute_injection_alerts(manifest, call_status=log.status or "")
    return {
        "system_chars": int(manifest.get("system_chars") or 0),
        "truncated": bool(_manifest_any_truncated(manifest)),
        "module_included_count": len(modules.get("included") or []),
        "module_skipped_count": len(modules.get("skipped") or []),
        "alert_ids": [a.get("id") for a in alerts if a.get("id")],
        "checksum": manifest.get("checksum"),
    }


def _row(log: DramaLlmCallLog, category: str) -> dict[str, Any]:
    causes = infer_suspected_causes(log, category)
    allow_anti = category == "skill_structure" and CAUSE_OVER_INJECTION not in causes
    return {
        "id": str(log.id),
        "llm_log_id": str(log.id),
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "role": log.role,
        "purpose": log.purpose,
        "status": log.status,
        "category": category,
        "error_message": log.error_message,
        "model_name": log.model_name,
        "project_id": str(log.project_id) if log.project_id else None,
        "job_id": str(log.generation_job_id) if log.generation_job_id else None,
        "response_preview": (log.response_text or "")[:1200],
        "suspected_causes": causes,
        "injection_summary": _injection_summary(log),
        "suggested_anti_example": (
            {
                "id": f"AUTO-{str(log.id)[:8]}",
                "severity": "high",
                "title": (log.error_message or log.purpose or "structured_fail")[:120],
                "note": "审阅后写入 roles/*/anti-examples.yaml",
                "raw_error": log.error_message,
            }
            if allow_anti
            else None
        ),
    }


def collect_classified(*, lookback: int = 300, role: str = "") -> dict[str, list[dict[str, Any]]]:
    qs = DramaLlmCallLog.objects.order_by("-created_at")[:lookback]
    if role:
        qs = DramaLlmCallLog.objects.filter(role=role).order_by("-created_at")[:lookback]

    buckets: dict[str, list[dict[str, Any]]] = {
        "skill_structure": [],
        "provider_config": [],
        "infra": [],
    }
    for log in qs:
        category = _classify(log)
        if not category:
            continue
        buckets[category].append(_row(log, category))
    return buckets


def export_skill_failures(*, limit: int = 50, role: str = "") -> list[dict[str, Any]]:
    """仅导出可回流技能反例的结构化失败。"""
    buckets = collect_classified(lookback=max(limit * 6, 200), role=role)
    return buckets["skill_structure"][:limit]


def load_eval_summary() -> dict[str, Any] | None:
    path = _skills_root() / "eval" / "reports" / "summary.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def repair_stats(*, lookback: int = 200) -> dict[str, Any]:
    recent = list(
        DramaLlmCallLog.objects.order_by("-created_at")[:lookback].values(
            "purpose", "status"
        )
    )
    repair_calls = [r for r in recent if "json_repair" in (r.get("purpose") or "")]
    repair_ok = sum(1 for r in repair_calls if r.get("status") == "success")
    return {
        "sample_size": len(recent),
        "repair_calls": len(repair_calls),
        "repair_success": repair_ok,
        "repair_success_rate": (
            round(repair_ok / len(repair_calls), 4) if repair_calls else None
        ),
    }


def skill_ops_overview(*, limit: int = 30, role: str = "") -> dict[str, Any]:
    buckets = collect_classified(lookback=400, role=role)
    skill_failures = buckets["skill_structure"][:limit]
    return {
        "failures": skill_failures,
        "failure_count": len(skill_failures),
        "noise_counts": {
            "provider_config": len(buckets["provider_config"]),
            "infra": len(buckets["infra"]),
        },
        "eval_summary": load_eval_summary(),
        "repair_stats": repair_stats(),
        "purpose": "只列出可用来改 anti-examples / SKILL 的结构化失败；超时与模型参数问题请去调用日志或模型管理。",
    }
