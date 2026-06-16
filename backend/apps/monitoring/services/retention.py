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

MONITORING_DATA_TARGETS = {
    "exceptions": {
        "label": "异常记录",
        "model": MonitoringException,
        "time_field": "created_at",
    },
    "api_performance": {
        "label": "接口性能日志",
        "model": ApiPerformanceLog,
        "time_field": "created_at",
    },
    "frontend_events": {
        "label": "前端事件",
        "model": FrontendEvent,
        "time_field": "created_at",
    },
    "slow_sql": {
        "label": "慢 SQL 日志",
        "model": SqlPerformanceLog,
        "time_field": "created_at",
    },
    "alert_events": {
        "label": "告警事件",
        "model": AlertEvent,
        "time_field": "triggered_at",
    },
    "health_snapshots": {
        "label": "健康快照",
        "model": ServiceHealthSnapshot,
        "time_field": "checked_at",
    },
}


def normalize_monitoring_targets(targets: list[str] | None = None) -> list[str]:
    if not targets:
        return list(MONITORING_DATA_TARGETS.keys())
    allowed = set(MONITORING_DATA_TARGETS)
    normalized = []
    for item in targets:
        key = str(item or "").strip()
        if key in allowed and key not in normalized:
            normalized.append(key)
    return normalized


def _target_queryset(key: str, *, cutoff=None):
    config = MONITORING_DATA_TARGETS[key]
    queryset = config["model"].objects.all()
    if cutoff is None:
        return queryset
    return queryset.filter(**{f"{config['time_field']}__lt": cutoff})


def get_monitoring_data_counts() -> dict[str, dict]:
    data = {}
    for key, config in MONITORING_DATA_TARGETS.items():
        data[key] = {
            "label": config["label"],
            "count": config["model"].objects.count(),
        }
    return data


def cleanup_expired_monitoring_data(
    retention_days: int | None = None,
    *,
    targets: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    days = retention_days if retention_days is not None else int(getattr(settings, "MONITORING_RETENTION_DAYS", 30))
    days = max(1, int(days))
    cutoff = timezone.now() - timedelta(days=days)
    result = {}
    for key in normalize_monitoring_targets(targets):
        queryset = _target_queryset(key, cutoff=cutoff)
        if dry_run:
            result[key] = queryset.count()
            continue
        count, _ = queryset.delete()
        result[key] = count
    return result


def purge_monitoring_data(*, targets: list[str] | None = None, dry_run: bool = False) -> dict[str, int]:
    result = {}
    for key in normalize_monitoring_targets(targets):
        queryset = _target_queryset(key)
        if dry_run:
            result[key] = queryset.count()
            continue
        count, _ = queryset.delete()
        result[key] = count
    return result
