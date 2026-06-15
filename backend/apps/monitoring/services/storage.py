import logging
import time
from typing import Any

from django.conf import settings
from django.db import DatabaseError, OperationalError, ProgrammingError, connection
from django.utils import timezone

from apps.monitoring.models import (
    ApiPerformanceLog,
    FrontendEvent,
    MonitoringException,
    SqlPerformanceLog,
)
from apps.monitoring.services.sanitizer import (
    compact_sql,
    sanitize_payload,
    stable_hash,
)

logger = logging.getLogger(__name__)

REQUIRED_TABLES = {
    "sf_api_performance_log",
    "sf_frontend_event",
    "sf_monitoring_exception",
    "sf_sql_performance_log",
    "sf_alert_rule",
    "sf_alert_event",
    "sf_service_health_snapshot",
}
TABLE_CHECK_INTERVAL_SECONDS = 60
_tables_ready: bool | None = None
_last_table_check = 0.0
_last_missing_signature = ""


def is_monitoring_enabled() -> bool:
    return bool(getattr(settings, "MONITORING_ENABLED", True)) and monitoring_tables_ready()


def monitoring_tables_ready() -> bool:
    global _last_missing_signature, _last_table_check, _tables_ready

    now = time.monotonic()
    if _tables_ready is not None and now - _last_table_check < TABLE_CHECK_INTERVAL_SECONDS:
        return _tables_ready

    _last_table_check = now
    try:
        existing_tables = set(connection.introspection.table_names())
    except DatabaseError as exc:
        _tables_ready = False
        signature = exc.__class__.__name__
        if signature != _last_missing_signature:
            logger.warning("监控表检查失败，跳过监控写入: %s", exc)
            _last_missing_signature = signature
        return False

    missing = sorted(REQUIRED_TABLES - existing_tables)
    _tables_ready = not missing
    if missing:
        signature = ",".join(missing)
        if signature != _last_missing_signature:
            logger.warning("监控表未迁移，跳过监控写入: %s", signature)
            _last_missing_signature = signature
    return _tables_ready


def mark_monitoring_tables_unavailable(exc: Exception) -> None:
    global _last_missing_signature, _last_table_check, _tables_ready
    _tables_ready = False
    _last_table_check = time.monotonic()
    signature = exc.__class__.__name__
    if signature != _last_missing_signature:
        logger.warning("监控写入失败，已临时跳过后续监控写入: %s", exc)
        _last_missing_signature = signature


def store_frontend_events(events: list[dict[str, Any]]) -> int:
    if not is_monitoring_enabled() or not events:
        return 0
    max_batch = int(getattr(settings, "MONITORING_MAX_BATCH_SIZE", 50))
    objects = []
    for item in events[:max_batch]:
        payload = sanitize_payload(item.get("payload"))
        performance = sanitize_payload(item.get("performance"))
        objects.append(
            FrontendEvent(
                event_type=item["event_type"],
                level=item.get("level") or "info",
                name=(item.get("name") or "")[:120],
                message=item.get("message") or "",
                page_url=(item.get("page_url") or "")[:1024],
                route=(item.get("route") or "")[:512],
                browser=(item.get("browser") or "")[:120],
                os=(item.get("os") or "")[:120],
                user_id=item.get("user_id"),
                session_id=(item.get("session_id") or "")[:64],
                trace_id=(item.get("trace_id") or "")[:64],
                payload=payload,
                performance=performance,
                created_at=item.get("created_at") or timezone.now(),
            )
        )
    try:
        FrontendEvent.objects.bulk_create(objects, batch_size=max_batch)
        return len(objects)
    except (ProgrammingError, OperationalError) as exc:
        mark_monitoring_tables_unavailable(exc)
        return 0
    except Exception:
        logger.exception("前端监控事件写入失败")
        return 0


def store_backend_exception(**kwargs) -> MonitoringException | None:
    if not is_monitoring_enabled():
        return None
    message = kwargs.get("message") or ""
    exception_type = kwargs.get("exception_type") or ""
    fingerprint = kwargs.get("fingerprint") or stable_hash("backend", exception_type, message, kwargs.get("path"))
    try:
        return MonitoringException.objects.create(
            source=MonitoringException.Source.BACKEND,
            level=kwargs.get("level") or "error",
            exception_type=exception_type[:120],
            message=message,
            stack=kwargs.get("stack") or "",
            path=(kwargs.get("path") or "")[:512],
            method=(kwargs.get("method") or "")[:12],
            status_code=kwargs.get("status_code"),
            user_id=kwargs.get("user_id"),
            ip_address=kwargs.get("ip_address"),
            user_agent=(kwargs.get("user_agent") or "")[:512],
            trace_id=(kwargs.get("trace_id") or "")[:64],
            fingerprint=fingerprint,
            request_data=sanitize_payload(kwargs.get("request_data")),
            response_data=sanitize_payload(kwargs.get("response_data")),
            extra=sanitize_payload(kwargs.get("extra")),
        )
    except (ProgrammingError, OperationalError) as exc:
        mark_monitoring_tables_unavailable(exc)
        return None
    except Exception:
        logger.exception("后端异常监控写入失败")
        return None


def store_frontend_exception(event: FrontendEvent) -> MonitoringException | None:
    if not is_monitoring_enabled():
        return None
    payload = event.payload or {}
    message = event.message or payload.get("message") or ""
    exception_type = payload.get("error_type") or event.event_type
    fingerprint = stable_hash("frontend", exception_type, message, event.route)
    try:
        return MonitoringException.objects.create(
            source=MonitoringException.Source.FRONTEND,
            level=event.level,
            exception_type=str(exception_type)[:120],
            message=message,
            stack=payload.get("stack") or "",
            path=event.route or event.page_url[:512],
            user_id=event.user_id,
            user_agent=payload.get("user_agent", "")[:512],
            trace_id=event.trace_id,
            fingerprint=fingerprint,
            request_data=sanitize_payload(payload.get("request")),
            response_data=sanitize_payload(payload.get("response")),
            extra=sanitize_payload({"page_url": event.page_url, "session_id": event.session_id}),
            created_at=event.created_at,
        )
    except (ProgrammingError, OperationalError) as exc:
        mark_monitoring_tables_unavailable(exc)
        return None
    except Exception:
        logger.exception("前端异常索引写入失败")
        return None


def store_api_performance(**kwargs) -> ApiPerformanceLog | None:
    if not is_monitoring_enabled():
        return None
    try:
        return ApiPerformanceLog.objects.create(
            path=(kwargs.get("path") or "")[:512],
            method=(kwargs.get("method") or "")[:12],
            status_code=kwargs.get("status_code"),
            duration_ms=max(0, int(kwargs.get("duration_ms") or 0)),
            query_count=max(0, int(kwargs.get("query_count") or 0)),
            slow_sql_count=max(0, int(kwargs.get("slow_sql_count") or 0)),
            request_size=max(0, int(kwargs.get("request_size") or 0)),
            response_size=max(0, int(kwargs.get("response_size") or 0)),
            user_id=kwargs.get("user_id"),
            ip_address=kwargs.get("ip_address"),
            user_agent=(kwargs.get("user_agent") or "")[:512],
            trace_id=(kwargs.get("trace_id") or "")[:64],
            request_data=sanitize_payload(kwargs.get("request_data")),
            response_data=sanitize_payload(kwargs.get("response_data")),
            extra=sanitize_payload(kwargs.get("extra")),
        )
    except (ProgrammingError, OperationalError) as exc:
        mark_monitoring_tables_unavailable(exc)
        return None
    except Exception:
        logger.exception("接口性能监控写入失败")
        return None


def store_slow_sql(**kwargs) -> SqlPerformanceLog | None:
    if not is_monitoring_enabled():
        return None
    sql = compact_sql(kwargs.get("sql") or "")
    try:
        return SqlPerformanceLog.objects.create(
            path=(kwargs.get("path") or "")[:512],
            method=(kwargs.get("method") or "")[:12],
            sql=sql,
            sql_hash=stable_hash(sql),
            duration_ms=max(0, int(kwargs.get("duration_ms") or 0)),
            trace_id=(kwargs.get("trace_id") or "")[:64],
            user_id=kwargs.get("user_id"),
            stack=kwargs.get("stack") or "",
            extra=sanitize_payload(kwargs.get("extra")),
        )
    except (ProgrammingError, OperationalError) as exc:
        mark_monitoring_tables_unavailable(exc)
        return None
    except Exception:
        logger.exception("慢 SQL 监控写入失败")
        return None
