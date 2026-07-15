# -*- coding: utf-8 -*-
"""健康检查端点。"""
from __future__ import annotations

from django.db import connection
from django.core.cache import cache
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.core.responses import api_response


class HealthCheckView(APIView):
    """数据库与 Redis 连通性探测。"""

    permission_classes = [AllowAny]

    def get(self, request):
        checks: dict[str, str] = {}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {exc}"

        try:
            cache.set("health_probe", "1", timeout=5)
            checks["redis"] = "ok" if cache.get("health_probe") == "1" else "error"
        except Exception as exc:
            checks["redis"] = f"error: {exc}"

        healthy = all(value == "ok" for value in checks.values())
        return api_response(
            {"healthy": healthy, "checks": checks},
            message="ok" if healthy else "degraded",
            status=200 if healthy else 503,
        )
