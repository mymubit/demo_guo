# -*- coding: utf-8 -*-
"""V3 用量汇总 REST（默认读日 rollup；live=1 仅从 call log 按日期范围聚合）。"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_error, api_response
from apps.drama.models import DramaLlmCallLog, V3UsageDailyRollup
from apps.drama.orchestrator import usage_rollup as rollup_mod
from apps.drama.orchestrator.usage_rollup import estimate_cost, shanghai_date
from apps.drama.services.llm_call_log_service import resolve_model_label

_SHANGHAI = ZoneInfo("Asia/Shanghai")
_GROUP_BY_CHOICES = frozenset({"day", "model", "command_type"})
_ZERO = Decimal("0")
_METRIC_KEYS = (
    "prompt_tokens",
    "cached_prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "call_count",
    "success_count",
    "unpriced_call_count",
)


def _empty_metrics() -> dict[str, Any]:
    return {
        "prompt_tokens": 0,
        "cached_prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "call_count": 0,
        "success_count": 0,
        "estimated_cost": _ZERO,
        "unpriced_call_count": 0,
    }


def _format_cost(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def _serialize_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    cost = metrics.get("estimated_cost", _ZERO)
    if not isinstance(cost, Decimal):
        cost = Decimal(str(cost or 0))
    return {
        "prompt_tokens": int(metrics.get("prompt_tokens") or 0),
        "cached_prompt_tokens": int(metrics.get("cached_prompt_tokens") or 0),
        "completion_tokens": int(metrics.get("completion_tokens") or 0),
        "total_tokens": int(metrics.get("total_tokens") or 0),
        "call_count": int(metrics.get("call_count") or 0),
        "success_count": int(metrics.get("success_count") or 0),
        "estimated_cost": _format_cost(cost),
        "unpriced_call_count": int(metrics.get("unpriced_call_count") or 0),
    }


def _add_metrics(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key in _METRIC_KEYS:
        target[key] = int(target.get(key) or 0) + int(source.get(key) or 0)
    cost = source.get("estimated_cost", _ZERO)
    if not isinstance(cost, Decimal):
        cost = Decimal(str(cost or 0))
    existing = target.get("estimated_cost", _ZERO)
    if not isinstance(existing, Decimal):
        existing = Decimal(str(existing or 0))
    target["estimated_cost"] = existing + cost


def _parse_date_param(raw: str | None, *, default: date) -> date | None:
    if raw in (None, ""):
        return default
    parsed = parse_date(str(raw).strip())
    return parsed


def _rollup_key(group_by: str, row: V3UsageDailyRollup) -> str:
    if group_by == "day":
        return row.date.isoformat()
    if group_by == "model":
        return row.model_name or ""
    return row.command_type or ""


def _live_key(group_by: str, call_log: DramaLlmCallLog) -> str:
    if group_by == "day":
        return shanghai_date(call_log.created_at).isoformat()
    if group_by == "model":
        return call_log.model_name or ""
    return rollup_mod._resolve_command_type(call_log) or ""


def _metrics_from_rollup_row(row: V3UsageDailyRollup) -> dict[str, Any]:
    """读汇总时按当前单价重算费用，避免「后配定价看不到费用」。"""
    cost = estimate_cost(
        provider_id=row.provider_id,
        model_name=row.model_name or "",
        prompt_tokens=row.prompt_tokens,
        completion_tokens=row.completion_tokens,
        cached_prompt_tokens=getattr(row, "cached_prompt_tokens", 0) or 0,
    )
    if cost is not None:
        return {
            "prompt_tokens": row.prompt_tokens,
            "cached_prompt_tokens": getattr(row, "cached_prompt_tokens", 0) or 0,
            "completion_tokens": row.completion_tokens,
            "total_tokens": row.total_tokens,
            "call_count": row.call_count,
            "success_count": row.success_count,
            "estimated_cost": cost,
            "unpriced_call_count": 0,
        }
    return {
        "prompt_tokens": row.prompt_tokens,
        "cached_prompt_tokens": getattr(row, "cached_prompt_tokens", 0) or 0,
        "completion_tokens": row.completion_tokens,
        "total_tokens": row.total_tokens,
        "call_count": row.call_count,
        "success_count": row.success_count,
        "estimated_cost": row.estimated_cost,
        "unpriced_call_count": row.unpriced_call_count,
    }


def _aggregate_rollup(
    qs: QuerySet[V3UsageDailyRollup],
    *,
    group_by: str,
) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in qs.iterator():
        key = _rollup_key(group_by, row)
        bucket = buckets.setdefault(key, _empty_metrics())
        _add_metrics(bucket, _metrics_from_rollup_row(row))
    return buckets


def _metrics_from_call(call_log: DramaLlmCallLog) -> dict[str, Any]:
    prompt_tokens = int(call_log.prompt_tokens or 0)
    cached_prompt_tokens = int(call_log.cached_prompt_tokens or 0)
    if cached_prompt_tokens > prompt_tokens:
        cached_prompt_tokens = prompt_tokens
    completion_tokens = int(call_log.completion_tokens or 0)
    total_tokens = int(
        call_log.total_tokens
        if call_log.total_tokens is not None
        else prompt_tokens + completion_tokens
    )
    provider_id = rollup_mod._resolve_provider_id(call_log)
    cost = estimate_cost(
        provider_id=provider_id,
        model_name=call_log.model_name or "",
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cached_prompt_tokens=cached_prompt_tokens,
    )
    is_priced = cost is not None
    return {
        "prompt_tokens": prompt_tokens,
        "cached_prompt_tokens": cached_prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "call_count": 1,
        "success_count": 1 if call_log.status == DramaLlmCallLog.Status.SUCCESS else 0,
        "estimated_cost": cost if is_priced else _ZERO,
        "unpriced_call_count": 0 if is_priced else 1,
    }


def _aggregate_live_logs(
    qs: QuerySet[DramaLlmCallLog],
    *,
    group_by: str,
) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for call_log in qs.select_related("v3_command_run", "v3_project").iterator():
        key = _live_key(group_by, call_log)
        bucket = buckets.setdefault(key, _empty_metrics())
        _add_metrics(bucket, _metrics_from_call(call_log))
    return buckets


def _build_response(
    *,
    date_from: date,
    date_to: date,
    group_by: str,
    buckets: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    rows = []
    totals = _empty_metrics()
    for key in sorted(buckets.keys()):
        metrics = buckets[key]
        _add_metrics(totals, metrics)
        row = {"key": key, **_serialize_metrics(metrics)}
        if group_by == "model":
            row["label"] = resolve_model_label(key)
        rows.append(row)
    return {
        "timezone": "Asia/Shanghai",
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "group_by": group_by,
        "rows": rows,
        "totals": _serialize_metrics(totals),
    }


class V3UsageSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        group_by = (request.query_params.get("group_by") or "day").strip()
        if group_by not in _GROUP_BY_CHOICES:
            return api_error(400, "group_by 须为 day|model|command_type")

        today = timezone.now().astimezone(_SHANGHAI).date()
        date_from = _parse_date_param(
            request.query_params.get("date_from"),
            default=today - timedelta(days=30),
        )
        date_to = _parse_date_param(
            request.query_params.get("date_to"),
            default=today,
        )
        if date_from is None or date_to is None:
            return api_error(400, "date_from / date_to 须为 YYYY-MM-DD")
        if date_from > date_to:
            return api_error(400, "date_from 不能晚于 date_to")

        live_raw = (request.query_params.get("live") or "0").strip()
        is_live = live_raw in ("1", "true", "True")

        rollup_qs = V3UsageDailyRollup.objects.filter(
            owner=request.user,
            date__gte=date_from,
            date__lte=date_to,
        )
        project_id = (request.query_params.get("project_id") or "").strip()
        if project_id:
            rollup_qs = rollup_qs.filter(project_id=project_id)

        if is_live:
            range_start = datetime(
                date_from.year, date_from.month, date_from.day, tzinfo=_SHANGHAI
            )
            range_end = datetime(
                date_to.year, date_to.month, date_to.day, tzinfo=_SHANGHAI
            ) + timedelta(days=1)
            log_qs = DramaLlmCallLog.objects.filter(
                created_at__gte=range_start,
                created_at__lt=range_end,
            ).filter(
                Q(v3_command_run__owner=request.user)
                | Q(v3_project__owner=request.user)
            )
            if project_id:
                log_qs = log_qs.filter(v3_project_id=project_id)
            buckets = _aggregate_live_logs(log_qs, group_by=group_by)
        else:
            buckets = _aggregate_rollup(rollup_qs, group_by=group_by)

        return api_response(
            _build_response(
                date_from=date_from,
                date_to=date_to,
                group_by=group_by,
                buckets=buckets,
            )
        )
