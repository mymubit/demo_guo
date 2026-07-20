# -*- coding: utf-8 -*-
"""技能运维：只收集「能用来改技能」的结构化失败，过滤超时/连通噪音。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.drama.models import DramaLlmCallLog

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
    if re.search(r"Schema|不是合法 JSON|JSON 对象|产物 Schema", err, re.I):
        return "skill_structure"
    # 生成类错误但无明确结构信息：不进技能运维主列表
    return None


def _row(log: DramaLlmCallLog, category: str) -> dict[str, Any]:
    return {
        "id": str(log.id),
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
        "suggested_anti_example": (
            {
                "id": f"AUTO-{str(log.id)[:8]}",
                "severity": "high",
                "title": (log.error_message or log.purpose or "structured_fail")[:120],
                "note": "审阅后写入 roles/*/anti-examples.yaml",
                "raw_error": log.error_message,
            }
            if category == "skill_structure"
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
