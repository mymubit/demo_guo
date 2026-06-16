from datetime import timedelta

from django.db.models import Avg, Count, Max, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.common.permissions import IsAdminUser
from apps.console.responses import api_ok
from apps.monitoring.models import (
    AlertEvent,
    AlertRule,
    ApiPerformanceLog,
    FrontendEvent,
    MonitoringException,
    ServiceHealthSnapshot,
    SqlPerformanceLog,
)
from apps.monitoring.serializers import (
    AlertEventSerializer,
    AlertRuleSerializer,
    ApiPerformanceLogSerializer,
    FrontendEventBatchSerializer,
    FrontendEventSerializer,
    MonitoringExceptionSerializer,
    SqlPerformanceLogSerializer,
)
from apps.monitoring.services.alerts import evaluate_alert_rules
from apps.monitoring.services.retention import (
    MONITORING_DATA_TARGETS,
    cleanup_expired_monitoring_data,
    get_monitoring_data_counts,
    purge_monitoring_data,
)
from apps.monitoring.services.storage import store_frontend_events, store_frontend_exception
from apps.monitoring.throttles import MonitoringAnonThrottle, MonitoringUserThrottle


class MonitoringReportView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [MonitoringAnonThrottle, MonitoringUserThrottle]

    def post(self, request):
        raw = request.data or {}
        payload = raw if isinstance(raw, dict) and "events" in raw else {"events": [raw]}
        serializer = FrontendEventBatchSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        events = serializer.validated_data["events"]
        stored_count = store_frontend_events(events)
        if stored_count:
            error_types = {
                "js_error",
                "resource_error",
                "promise_error",
                "api_error",
                "api_business_error",
            }
            recent = FrontendEvent.objects.order_by("-created_at")[:stored_count]
            for event in recent:
                if event.event_type in error_types:
                    store_frontend_exception(event)
        return api_ok({"received": len(events), "stored": stored_count})


class AdminMonitoringBase:
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination

    def _time_range(self, request):
        days = min(max(int(request.query_params.get("days", 1) or 1), 1), 90)
        return timezone.now() - timedelta(days=days)

    def _apply_common_filters(self, queryset, request):
        since = self._time_range(request)
        queryset = queryset.filter(created_at__gte=since)
        field_names = {field.name for field in queryset.model._meta.fields}
        keyword = (request.query_params.get("keyword") or "").strip()
        level = (request.query_params.get("level") or "").strip()
        path = (request.query_params.get("path") or "").strip()
        if keyword:
            keyword_filter = Q()
            if "message" in field_names:
                keyword_filter |= Q(message__icontains=keyword)
            if "trace_id" in field_names:
                keyword_filter |= Q(trace_id__icontains=keyword)
            if "sql_hash" in field_names:
                keyword_filter |= Q(sql_hash__icontains=keyword)
            if keyword_filter:
                queryset = queryset.filter(keyword_filter)
        if level and "level" in field_names:
            queryset = queryset.filter(level=level)
        if path and "path" in field_names:
            queryset = queryset.filter(path__icontains=path)
        return queryset


def _daily_counts(queryset, since, date_field="created_at"):
    rows = []
    now = timezone.now()
    cursor = since.replace(hour=0, minute=0, second=0, microsecond=0)
    while cursor <= now:
        next_day = cursor + timedelta(days=1)
        rows.append(
            {
                "date": cursor.strftime("%Y-%m-%d"),
                "count": queryset.filter(**{f"{date_field}__gte": cursor, f"{date_field}__lt": next_day}).count(),
            }
        )
        cursor = next_day
    return rows


def _level_count(queryset, level: str) -> int:
    return queryset.filter(level=level).count()


def _ai_api_filter() -> Q:
    """按路径粗分 AI/编排类接口，避免拉高普通 CRUD 接口耗时均值。"""
    return (
        Q(path__icontains="/ai/")
        | Q(path__icontains="/llm")
        | Q(path__icontains="/agents/")
        | Q(path__icontains="/orchestration/")
        | Q(path__icontains="/main-chain/")
        | Q(path__icontains="/model/llm")
        | Q(path__icontains="/creation/submit/")
        | Q(path__icontains="/regenerate/")
    )


def _top_api_duration(queryset):
    return list(
        queryset.values("path")
        .annotate(avg_duration=Avg("duration_ms"), count=Count("id"), max_duration=Max("duration_ms"))
        .order_by("-avg_duration")[:10]
    )


class MonitoringOverviewView(AdminMonitoringBase, APIView):
    def get(self, request):
        since = self._time_range(request)
        frontend_events = FrontendEvent.objects.filter(created_at__gte=since)
        frontend_errors = frontend_events.filter(level__in=["error", "critical"])
        frontend_warnings = frontend_events.filter(level="warning")
        backend_events = MonitoringException.objects.filter(
            created_at__gte=since,
            source=MonitoringException.Source.BACKEND,
        )
        business_events = MonitoringException.objects.filter(
            created_at__gte=since,
            source=MonitoringException.Source.BUSINESS,
        )
        backend_business_events = MonitoringException.objects.filter(
            created_at__gte=since,
            source__in=[MonitoringException.Source.BACKEND, MonitoringException.Source.BUSINESS],
        )
        api_logs = ApiPerformanceLog.objects.filter(created_at__gte=since)
        ai_api_filter = _ai_api_filter()
        ai_api_logs = api_logs.filter(ai_api_filter)
        normal_api_logs = api_logs.exclude(ai_api_filter)
        slow_sql = SqlPerformanceLog.objects.filter(created_at__gte=since)
        alerts = AlertEvent.objects.filter(triggered_at__gte=since)
        top_paths = _top_api_duration(api_logs)
        top_normal_paths = _top_api_duration(normal_api_logs)
        top_ai_paths = _top_api_duration(ai_api_logs)
        frontend_problem_events = frontend_events.filter(level__in=["warning", "error", "critical"])
        frontend_problem_distribution = list(
            frontend_problem_events.values("event_type").annotate(count=Count("id")).order_by("-count")
        )
        trend_base = backend_business_events.filter(
            level__in=["warning", "error", "critical"]
        )
        severity_summary = {
            "critical": _level_count(frontend_events, "critical") + _level_count(backend_business_events, "critical"),
            "error": _level_count(frontend_events, "error") + _level_count(backend_business_events, "error"),
            "warning": _level_count(frontend_events, "warning") + _level_count(backend_business_events, "warning"),
            "info": _level_count(frontend_events, "info") + _level_count(backend_business_events, "info"),
        }
        severity_distribution = [
            {"level": "critical", "label": "严重", "count": severity_summary["critical"]},
            {"level": "error", "label": "错误", "count": severity_summary["error"]},
            {"level": "warning", "label": "警告", "count": severity_summary["warning"]},
            {"level": "info", "label": "信息", "count": severity_summary["info"]},
        ]
        business_error_rate = 0.0
        api_total = api_logs.count()
        if api_total:
            business_error_rate = round(
                api_logs.filter(extra__business_error=True).count() / api_total * 100,
                2,
            )
        data = {
            "summary": {
                "critical_count": severity_summary["critical"],
                "error_count": severity_summary["error"],
                "warning_count": severity_summary["warning"],
                "info_count": severity_summary["info"],
                "frontend_errors": frontend_errors.count(),
                "frontend_warnings": frontend_warnings.count(),
                "backend_errors": backend_events.filter(level__in=["error", "critical"]).count(),
                "backend_warnings": backend_events.filter(level="warning").count(),
                "business_errors": business_events.filter(level__in=["error", "critical"]).count(),
                "business_warnings": business_events.filter(level="warning").count(),
                "business_error_rate": business_error_rate,
                "api_requests": api_total,
                "api_avg_duration": round(api_logs.aggregate(value=Avg("duration_ms"))["value"] or 0, 2),
                "normal_api_requests": normal_api_logs.count(),
                "normal_api_avg_duration": round(normal_api_logs.aggregate(value=Avg("duration_ms"))["value"] or 0, 2),
                "ai_api_requests": ai_api_logs.count(),
                "ai_api_avg_duration": round(ai_api_logs.aggregate(value=Avg("duration_ms"))["value"] or 0, 2),
                "slow_sql": slow_sql.count(),
                "open_alerts": alerts.filter(status=AlertEvent.Status.OPEN).count(),
            },
            "error_trend": _daily_counts(trend_base, since),
            "top_api_duration": top_paths,
            "top_normal_api_duration": top_normal_paths,
            "top_ai_api_duration": top_ai_paths,
            "severity_distribution": severity_distribution,
            "frontend_error_distribution": frontend_problem_distribution,
            "recent_alerts": AlertEventSerializer(alerts.order_by("-triggered_at")[:8], many=True).data,
        }
        return api_ok(data)


class MonitoringListMixin(AdminMonitoringBase, viewsets.ReadOnlyModelViewSet):
    pagination_class = StandardPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return api_ok(self.get_serializer(queryset, many=True).data)


class FrontendEventViewSet(MonitoringListMixin):
    serializer_class = FrontendEventSerializer

    def get_queryset(self):
        queryset = FrontendEvent.objects.all()
        event_type = (self.request.query_params.get("event_type") or "").strip()
        route = (self.request.query_params.get("route") or "").strip()
        queryset = self._apply_common_filters(queryset, self.request)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if route:
            queryset = queryset.filter(route__icontains=route)
        return queryset.order_by("-created_at")


class MonitoringExceptionViewSet(MonitoringListMixin):
    serializer_class = MonitoringExceptionSerializer

    def get_queryset(self):
        queryset = MonitoringException.objects.all()
        source = (self.request.query_params.get("source") or "").strip()
        queryset = self._apply_common_filters(queryset, self.request)
        if source:
            queryset = queryset.filter(source=source)
        return queryset.order_by("-created_at")


class ApiPerformanceViewSet(MonitoringListMixin):
    serializer_class = ApiPerformanceLogSerializer

    def get_queryset(self):
        queryset = ApiPerformanceLog.objects.all()
        min_duration = self.request.query_params.get("min_duration")
        business_error = (self.request.query_params.get("business_error") or "").strip().lower()
        category = (self.request.query_params.get("category") or "").strip().lower()
        queryset = self._apply_common_filters(queryset, self.request)
        if min_duration:
            queryset = queryset.filter(duration_ms__gte=int(min_duration))
        if business_error in {"1", "true", "yes"}:
            queryset = queryset.filter(extra__business_error=True)
        if category == "ai":
            queryset = queryset.filter(_ai_api_filter())
        elif category == "normal":
            queryset = queryset.exclude(_ai_api_filter())
        return queryset.order_by("-created_at")


class SlowSqlViewSet(MonitoringListMixin):
    serializer_class = SqlPerformanceLogSerializer

    def get_queryset(self):
        queryset = SqlPerformanceLog.objects.all()
        min_duration = self.request.query_params.get("min_duration")
        queryset = self._apply_common_filters(queryset, self.request)
        if min_duration:
            queryset = queryset.filter(duration_ms__gte=int(min_duration))
        return queryset.order_by("-created_at")


class AlertRuleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AlertRuleSerializer
    pagination_class = StandardPagination
    queryset = AlertRule.objects.all().order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return api_ok(self.get_serializer(self.get_queryset(), many=True).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return api_ok(serializer.data, http_status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop("partial", False))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_ok(serializer.data)


class AlertEventViewSet(MonitoringListMixin):
    serializer_class = AlertEventSerializer

    def get_queryset(self):
        since = self._time_range(self.request)
        status_value = (self.request.query_params.get("status") or "").strip()
        queryset = AlertEvent.objects.select_related("rule").filter(triggered_at__gte=since)
        if status_value:
            queryset = queryset.filter(status=status_value)
        return queryset.order_by("-triggered_at")


class MonitoringHealthView(AdminMonitoringBase, APIView):
    def get(self, request):
        triggered = evaluate_alert_rules()
        snapshot = ServiceHealthSnapshot.objects.create(
            service_name="scriptforge-api",
            status="ok",
            metrics={"alert_triggered": triggered, "checked_by": "admin_api"},
        )
        return api_ok(
            {
                "status": snapshot.status,
                "checked_at": snapshot.checked_at,
                "alert_triggered": triggered,
            }
        )


class MonitoringMaintenanceView(AdminMonitoringBase, APIView):
    confirm_text = "CLEAR_MONITORING_DATA"

    def get(self, request):
        return api_ok(
            {
                "targets": [
                    {"key": key, "label": config["label"]}
                    for key, config in MONITORING_DATA_TARGETS.items()
                ],
                "counts": get_monitoring_data_counts(),
                "confirm_text": self.confirm_text,
            }
        )

    def post(self, request):
        action = str((request.data or {}).get("action") or "").strip()
        targets = (request.data or {}).get("targets") or None
        dry_run = bool((request.data or {}).get("dry_run", False))

        if action == "cleanup_expired":
            retention_days = int((request.data or {}).get("retention_days") or 30)
            result = cleanup_expired_monitoring_data(
                retention_days,
                targets=targets,
                dry_run=dry_run,
            )
            return api_ok(
                {
                    "action": action,
                    "dry_run": dry_run,
                    "retention_days": retention_days,
                    "deleted": result,
                },
                message="预估完成" if dry_run else "过期监控数据已清理",
            )

        if action == "purge":
            confirm = str((request.data or {}).get("confirm_text") or "")
            if not dry_run and confirm != self.confirm_text:
                return api_ok(
                    {
                        "required_confirm_text": self.confirm_text,
                    },
                    code=4001,
                    message="清空历史数据前请输入确认文本",
                )
            result = purge_monitoring_data(targets=targets, dry_run=dry_run)
            return api_ok(
                {
                    "action": action,
                    "dry_run": dry_run,
                    "deleted": result,
                },
                message="预估完成" if dry_run else "监控历史数据已清空",
            )

        return api_ok({"allowed_actions": ["cleanup_expired", "purge"]}, code=4001, message="不支持的维护操作")
