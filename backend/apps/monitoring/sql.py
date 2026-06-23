# -*- coding: utf-8 -*-
import time
from contextlib import contextmanager

from django.conf import settings
from django.db import connection

from apps.monitoring.services.storage import store_slow_sql


@contextmanager
def capture_sql(request):
    request._monitoring_query_count = 0
    request._monitoring_slow_sql_count = 0
    slow_ms = int(getattr(settings, "MONITORING_SLOW_SQL_MS", 500))

    def wrapper(execute, sql, params, many, context):
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            request._monitoring_query_count += 1
            if duration_ms >= slow_ms:
                request._monitoring_slow_sql_count += 1
                user = getattr(request, "user", None)
                store_slow_sql(
                    path=request.path,
                    method=request.method,
                    sql=sql,
                    duration_ms=duration_ms,
                    trace_id=getattr(request, "monitoring_trace_id", ""),
                    user_id=getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None,
                    extra={"many": bool(many), "params_count": len(params or []) if params is not None else 0},
                )

    with connection.execute_wrapper(wrapper):
        yield
