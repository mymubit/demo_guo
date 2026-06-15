import logging
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.monitoring.models import AlertEvent, AlertRule, ApiPerformanceLog, FrontendEvent, SqlPerformanceLog

logger = logging.getLogger(__name__)


def compare_value(value: float, comparator: str, threshold: float) -> bool:
    if comparator == AlertRule.Comparator.GT:
        return value > threshold
    if comparator == AlertRule.Comparator.GTE:
        return value >= threshold
    if comparator == AlertRule.Comparator.LT:
        return value < threshold
    if comparator == AlertRule.Comparator.LTE:
        return value <= threshold
    return False


def _is_in_cooldown(rule: AlertRule) -> bool:
    if not rule.last_triggered_at:
        return False
    cooldown_until = rule.last_triggered_at + timedelta(minutes=rule.cooldown_minutes)
    return cooldown_until > timezone.now()


def _metric_value(rule: AlertRule, since):
    path_filter = Q()
    if rule.path_pattern:
        path_filter = Q(path__icontains=rule.path_pattern)

    if rule.metric_type == AlertRule.MetricType.FRONTEND_ERROR_COUNT:
        qs = FrontendEvent.objects.filter(created_at__gte=since, level__in=["error", "critical"])
        return float(qs.count()), {"sample_count": qs.count()}

    if rule.metric_type == AlertRule.MetricType.BACKEND_ERROR_COUNT:
        qs = ApiPerformanceLog.objects.filter(created_at__gte=since).filter(path_filter).filter(status_code__gte=500)
        return float(qs.count()), {"sample_count": qs.count()}

    if rule.metric_type == AlertRule.MetricType.API_AVG_DURATION:
        qs = ApiPerformanceLog.objects.filter(created_at__gte=since).filter(path_filter)
        value = qs.aggregate(value=Avg("duration_ms"))["value"] or 0
        return float(value), {"sample_count": qs.count()}

    if rule.metric_type == AlertRule.MetricType.API_ERROR_RATE:
        qs = ApiPerformanceLog.objects.filter(created_at__gte=since).filter(path_filter)
        total = qs.count()
        if total == 0:
            return 0.0, {"sample_count": 0, "error_count": 0}
        error_count = qs.filter(status_code__gte=400).count()
        return round(error_count / total * 100, 4), {"sample_count": total, "error_count": error_count}

    if rule.metric_type == AlertRule.MetricType.SLOW_SQL_COUNT:
        qs = SqlPerformanceLog.objects.filter(created_at__gte=since).filter(path_filter)
        return float(qs.count()), {"sample_count": qs.count()}

    return 0.0, {"sample_count": 0}


def send_alert(event: AlertEvent) -> None:
    """告警推送扩展点：第一版仅记录日志，后续接企业微信/邮件/短信。"""
    logger.warning("监控告警触发: %s", event.message)


def evaluate_alert_rules() -> int:
    triggered = 0
    now = timezone.now()
    for rule in AlertRule.objects.filter(is_enabled=True):
        if _is_in_cooldown(rule):
            continue
        since = now - timedelta(minutes=rule.window_minutes)
        value, snapshot = _metric_value(rule, since)
        if not compare_value(value, rule.comparator, rule.threshold):
            continue
        event = AlertEvent.objects.create(
            rule=rule,
            metric_type=rule.metric_type,
            level=rule.level,
            value=value,
            threshold=rule.threshold,
            message=f"{rule.name}：当前值 {value}，阈值 {rule.comparator} {rule.threshold}",
            snapshot={**snapshot, "window_minutes": rule.window_minutes, "path_pattern": rule.path_pattern},
        )
        rule.last_triggered_at = now
        rule.save(update_fields=["last_triggered_at", "updated_at"])
        send_alert(event)
        triggered += 1
    return triggered
