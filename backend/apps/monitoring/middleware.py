import json
import logging
import time
import traceback
import uuid
from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from apps.monitoring.services.sanitizer import sanitize_payload
from apps.monitoring.services.storage import store_api_performance, store_backend_exception
from apps.monitoring.sql import capture_sql

logger = logging.getLogger(__name__)


def get_client_ip(request: HttpRequest) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def should_skip_path(path: str) -> bool:
    skip_paths = tuple(getattr(settings, "MONITORING_SKIP_PATHS", ()))
    return any(path.startswith(prefix) for prefix in skip_paths)


def request_payload(request: HttpRequest) -> dict:
    if request.method.upper() in {"GET", "HEAD", "OPTIONS"}:
        return {"query": sanitize_payload(dict(request.GET))}
    content_type = request.META.get("CONTENT_TYPE", "")
    if "application/json" not in content_type:
        return {"content_type": content_type, "body_size": len(request.body or b"")}
    try:
        body = request.body.decode("utf-8")
        if not body:
            return {}
        return sanitize_payload(json.loads(body))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"body_size": len(request.body or b""), "parse_error": True}


def response_payload(response: HttpResponse) -> dict:
    if not getattr(settings, "MONITORING_CAPTURE_RESPONSE", False):
        return {}
    content_type = response.get("Content-Type", "")
    if "application/json" not in content_type:
        return {"content_type": content_type}
    try:
        content = response.content.decode("utf-8")
        return sanitize_payload(json.loads(content)) if content else {}
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        return {"parse_error": True}


class MonitoringRequestMiddleware(MiddlewareMixin):
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        super().__init__(get_response)
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not getattr(settings, "MONITORING_ENABLED", True) or should_skip_path(request.path):
            return self.get_response(request)

        trace_id = request.META.get("HTTP_X_TRACE_ID") or uuid.uuid4().hex
        request.monitoring_trace_id = trace_id
        started_at = time.perf_counter()
        request_data = {}

        try:
            request_data = request_payload(request)
            with capture_sql(request):
                response = self.get_response(request)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started_at) * 1000)
            user = getattr(request, "user", None)
            store_backend_exception(
                exception_type=exc.__class__.__name__,
                message=str(exc),
                stack=traceback.format_exc(),
                path=request.path,
                method=request.method,
                status_code=500,
                user_id=getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                trace_id=trace_id,
                request_data=request_data,
                extra={"duration_ms": duration_ms},
            )
            logger.exception("请求处理异常 trace_id=%s path=%s", trace_id, request.path)
            raise

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        user = getattr(request, "user", None)
        response["X-Trace-Id"] = trace_id
        store_api_performance(
            path=request.path,
            method=request.method,
            status_code=getattr(response, "status_code", None),
            duration_ms=duration_ms,
            query_count=getattr(request, "_monitoring_query_count", 0),
            slow_sql_count=getattr(request, "_monitoring_slow_sql_count", 0),
            request_size=len(request.body or b""),
            response_size=len(getattr(response, "content", b"") or b""),
            user_id=getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            trace_id=trace_id,
            request_data=request_data,
            response_data=response_payload(response),
            extra={"slow_api": duration_ms >= int(getattr(settings, "MONITORING_SLOW_API_MS", 1000))},
        )
        return response
