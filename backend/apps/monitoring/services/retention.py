from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.monitoring.models import (
    AlertEvent,
    ApiPerformanceLog,
    FrontendEvent,
    MonitoringException,
    ServiceHealthSnapshot,
    SqlPerformanceLog,
)


def cleanup_expired_monitoring_data(retention_days: int | None = None) -> dict[str, int]:
    days = retention_days or int(getattr(settings, "MONITORING_RETENTION_DAYS", 30))
    cutoff = timezone.now() - timedelta(days=days)
    targets = {
        "exceptions": MonitoringException.objects.filter(created_at__lt=cutoff),
        "api_performance": ApiPerformanceLog.objects.filter(created_at__lt=cutoff),
        "frontend_events": FrontendEvent.objects.filter(created_at__lt=cutoff),
        "slow_sql": SqlPerformanceLog.objects.filter(created_at__lt=cutoff),
        "alert_events": AlertEvent.objects.filter(triggered_at__lt=cutoff),
        "health_snapshots": ServiceHealthSnapshot.objects.filter(checked_at__lt=cutoff),
    }
    deleted = {}
    for key, queryset in targets.items():
        count, _ = queryset.delete()
        deleted[key] = count
    return deleted
