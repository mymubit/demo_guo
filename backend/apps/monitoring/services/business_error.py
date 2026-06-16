"""业务 API 失败采集：解析响应 code、分级日志、写入监控表。"""

from __future__ import annotations

import json
import logging
import random
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from apps.common.exceptions import SUCCESS, VALIDATION_ERROR
from apps.monitoring.models import MonitorLevel, MonitoringException
from apps.monitoring.services.sanitizer import stable_hash
from apps.monitoring.services.storage import is_monitoring_enabled

logger = logging.getLogger("apps.monitoring.business")

BUSINESS_EXCEPTION_TYPE = "BusinessApiError"


def get_business_error_sample_rate(code: int) -> float:
    setting_name = (
        "MONITORING_VALIDATION_ERROR_SAMPLE_RATE"
        if code == VALIDATION_ERROR
        else "MONITORING_BUSINESS_ERROR_SAMPLE_RATE"
    )
    default_value = 0.1 if code == VALIDATION_ERROR else 1.0
    raw_value = getattr(settings, setting_name, default_value)
    try:
        return max(0.0, min(1.0, float(raw_value)))
    except (TypeError, ValueError):
        return default_value


def should_sample_business_error(code: int) -> bool:
    if code == SUCCESS:
        return False
    rate = get_business_error_sample_rate(code)
    if rate >= 1.0:
        return True
    if rate <= 0:
        return False
    return random.random() <= rate


def resolve_business_error_level(code: int) -> str:
    if code == VALIDATION_ERROR:
        return MonitorLevel.INFO
    if code >= 500:
        return MonitorLevel.ERROR
    return MonitorLevel.WARNING


def should_store_business_error(code: int, *, is_sampled: bool | None = None) -> bool:
    if code == SUCCESS:
        return False
    if is_sampled is None:
        return should_sample_business_error(code)
    return is_sampled


def parse_business_response(response: HttpResponse) -> tuple[int, str] | None:
    body: dict[str, Any] | None = None
    data = getattr(response, "data", None)
    if isinstance(data, dict) and "code" in data:
        body = data
    else:
        content_type = response.get("Content-Type", "")
        if "application/json" not in content_type:
            return None
        try:
            raw = response.content.decode("utf-8")
            if not raw:
                return None
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                body = parsed
        except (AttributeError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return None

    if not isinstance(body, dict) or "code" not in body:
        return None
    try:
        code = int(body["code"])
    except (TypeError, ValueError):
        return None
    message = str(body.get("message") or "")
    return code, message


def build_business_error_extra(code: int, message: str, *, slow_api: bool) -> dict[str, Any]:
    return {
        "slow_api": slow_api,
        "business_error": code != SUCCESS,
        "business_code": code,
        "business_message": message[:500] if message else "",
    }


def log_business_api_error(
    *,
    code: int,
    message: str,
    path: str,
    method: str,
    trace_id: str = "",
    exception_type: str = BUSINESS_EXCEPTION_TYPE,
    is_sampled: bool | None = None,
) -> None:
    if code == SUCCESS:
        return
    if not getattr(settings, "MONITORING_BUSINESS_ERROR_LOG_ENABLED", True):
        return
    if not should_store_business_error(code, is_sampled=is_sampled):
        return

    log_method = logger.error if code >= 500 else logger.warning
    log_method(
        "业务 API 失败 code=%s path=%s method=%s trace_id=%s type=%s message=%s",
        code,
        path,
        method,
        trace_id,
        exception_type,
        message[:500],
    )


def store_business_api_error(
    *,
    code: int,
    message: str,
    path: str,
    method: str,
    trace_id: str = "",
    user_id=None,
    ip_address=None,
    user_agent: str = "",
    request_data: dict | None = None,
    exception_type: str = BUSINESS_EXCEPTION_TYPE,
    duration_ms: int | None = None,
    is_sampled: bool | None = None,
) -> MonitoringException | None:
    if code == SUCCESS or not is_monitoring_enabled():
        return None
    if not should_store_business_error(code, is_sampled=is_sampled):
        return None

    from apps.monitoring.services.storage import mark_monitoring_tables_unavailable

    fingerprint = stable_hash("business", code, message, path, method)
    try:
        return MonitoringException.objects.create(
            source=MonitoringException.Source.BUSINESS,
            level=resolve_business_error_level(code),
            exception_type=exception_type[:120],
            message=message[:4000],
            stack="",
            path=(path or "")[:512],
            method=(method or "")[:12],
            status_code=200,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=(user_agent or "")[:512],
            trace_id=(trace_id or "")[:64],
            fingerprint=fingerprint,
            request_data=request_data or {},
            response_data={"code": code, "message": message[:500]},
            extra={
                "business_code": code,
                "duration_ms": duration_ms,
            },
        )
    except Exception as exc:
        from django.db import DatabaseError, OperationalError, ProgrammingError

        if isinstance(exc, (ProgrammingError, OperationalError, DatabaseError)):
            mark_monitoring_tables_unavailable(exc)
            return None
        logger.exception("业务 API 错误监控写入失败")
        return None


def process_business_api_response(
    request: HttpRequest,
    response: HttpResponse,
    *,
    trace_id: str,
    duration_ms: int,
    request_data: dict | None,
    get_client_ip,
) -> dict[str, Any]:
    """解析响应中的业务 code，写日志/监控表，并返回需合并进 performance.extra 的字段。"""
    slow_api = duration_ms >= int(getattr(settings, "MONITORING_SLOW_API_MS", 1000))
    parsed = parse_business_response(response)
    if not parsed:
        return {"slow_api": slow_api, "business_error": False}

    code, message = parsed
    extra = build_business_error_extra(code, message, slow_api=slow_api)
    if code == SUCCESS:
        return extra

    is_sampled = should_sample_business_error(code)
    exc = getattr(request, "_monitoring_exception", None)
    exception_type = type(exc).__name__ if exc is not None else BUSINESS_EXCEPTION_TYPE
    user = getattr(request, "user", None)
    user_id = getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None

    log_business_api_error(
        code=code,
        message=message,
        path=request.path,
        method=request.method,
        trace_id=trace_id,
        exception_type=exception_type,
        is_sampled=is_sampled,
    )
    store_business_api_error(
        code=code,
        message=message,
        path=request.path,
        method=request.method,
        trace_id=trace_id,
        user_id=user_id,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        request_data=request_data,
        exception_type=exception_type,
        duration_ms=duration_ms,
        is_sampled=is_sampled,
    )
    return extra
