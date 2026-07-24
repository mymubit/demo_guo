# -*- coding: utf-8 -*-
"""V3 执行日志 REST（owner 隔离；以 V3CommandRun 为轴）。"""
from __future__ import annotations

from datetime import datetime

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.responses import api_response
from apps.drama.api.v3.serializers import CommandRunSerializer
from apps.drama.models import DramaLlmCallLog, V3CommandRun, V3FailoverAttempt
from apps.drama.services.llm_call_log_service import LlmCallLogService

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 50


def _serialize_failover_attempt(attempt: V3FailoverAttempt) -> dict:
    return {
        "id": str(attempt.id),
        "attempt_index": attempt.attempt_index,
        "provider_id": str(attempt.provider_id),
        "provider_name": attempt.provider.name if attempt.provider_id else "",
        "status": attempt.status,
        "error_code": attempt.error_code or "",
        "error_message": attempt.error_message or "",
        "llm_call_log_id": (
            str(attempt.llm_call_log_id) if attempt.llm_call_log_id else None
        ),
        "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
    }


def _parse_limit(raw: str | None) -> int:
    try:
        value = int(raw) if raw not in (None, "") else _DEFAULT_LIMIT
    except (TypeError, ValueError):
        return _DEFAULT_LIMIT
    if value < 1:
        return _DEFAULT_LIMIT
    return min(value, _MAX_LIMIT)


def _parse_offset(raw: str | None) -> int:
    try:
        value = int(raw) if raw not in (None, "") else 0
    except (TypeError, ValueError):
        return 0
    return max(0, value)


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    return parse_datetime(raw)


class V3LogRunListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        qs = V3CommandRun.objects.filter(owner=request.user).order_by("-created_at")
        project_id = (request.query_params.get("project_id") or "").strip()
        if project_id:
            qs = qs.filter(project_id=project_id)
        status = (request.query_params.get("status") or "").strip()
        if status:
            qs = qs.filter(status=status)
        command_type = (request.query_params.get("command_type") or "").strip()
        if command_type:
            qs = qs.filter(command_type=command_type)
        created_after = _parse_dt(request.query_params.get("created_after"))
        if created_after is not None:
            qs = qs.filter(created_at__gte=created_after)
        created_before = _parse_dt(request.query_params.get("created_before"))
        if created_before is not None:
            qs = qs.filter(created_at__lte=created_before)

        limit = _parse_limit(request.query_params.get("limit"))
        offset = _parse_offset(request.query_params.get("offset"))
        total = qs.count()
        items = CommandRunSerializer(qs[offset : offset + limit], many=True).data
        return api_response(
            {
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        )


class V3LogRunDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, run_id) -> Response:
        run = get_object_or_404(V3CommandRun, id=run_id, owner=request.user)
        data = dict(CommandRunSerializer(run).data)
        calls = (
            DramaLlmCallLog.objects.filter(v3_command_run=run)
            .order_by("created_at")
        )
        data["calls"] = [
            LlmCallLogService.serialize_v3_call(log, full=False) for log in calls
        ]
        attempts = (
            V3FailoverAttempt.objects.filter(v3_command_run=run)
            .select_related("provider")
            .order_by("attempt_index", "created_at")
        )
        data["failover_attempts"] = [
            _serialize_failover_attempt(item) for item in attempts
        ]
        return api_response(data)


class V3LogCallDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, call_id) -> Response:
        log = get_object_or_404(
            DramaLlmCallLog.objects.select_related("v3_command_run", "v3_project"),
            id=call_id,
        )
        run = log.v3_command_run
        project = log.v3_project
        owned = False
        if run is not None and run.owner_id == request.user.id:
            owned = True
        elif project is not None and project.owner_id == request.user.id:
            owned = True
        if not owned:
            return api_response(None, code=404, message="未找到", status=404)
        return api_response(LlmCallLogService.serialize_v3_call(log, full=True))
