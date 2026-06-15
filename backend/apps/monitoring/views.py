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
            error_types = {"js_error", "resource_error", "promise_error", "api_error"}
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


class MonitoringOverviewView(AdminMonitoringBase, APIView):
    def get(self, request):
        since = self._time_range(request)
        frontend_errors = FrontendEvent.objects.filter(created_at__gte=since, level__in=["error", "critical"])
        backend_errors = MonitoringException.objects.filter(created_at__gte=since, source="backend")
        api_logs = ApiPerformanceLog.objects.filter(created_at__gte=since)
        slow_sql = SqlPerformanceLog.objects.filter(created_at__gte=since)
        alerts = AlertEvent.objects.filter(triggered_at__gte=since)
        top_paths = list(
            api_logs.values("path")
            .annotate(avg_duration=Avg("duration_ms"), count=Count("id"), max_duration=Max("duration_ms"))
            .order_by("-avg_duration")[:10]
        )
        error_distribution = list(
            frontend_errors.values("event_type").annotate(count=Count("id")).order_by("-count")
        )
        trend_base = MonitoringException.objects.filter(created_at__gte=since)
        data = {
            "summary": {
                "frontend_errors": frontend_errors.count(),
                "backend_errors": backend_errors.count(),
                "api_requests": api_logs.count(),
                "api_avg_duration": round(api_logs.aggregate(value=Avg("duration_ms"))["value"] or 0, 2),
                "slow_sql": slow_sql.count(),
                "open_alerts": alerts.filter(status=AlertEvent.Status.OPEN).count(),
            },
            "error_trend": _daily_counts(trend_base, since),
            "top_api_duration": top_paths,
            "frontend_error_distribution": error_distribution,
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
        queryset = self._apply_common_filters(queryset, self.request)
        if min_duration:
            queryset = queryset.filter(duration_ms__gte=int(min_duration))
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
