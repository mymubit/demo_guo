# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from django.db import models
from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.monitoring.models import AlertEvent, AlertRule, ApiPerformanceLog, FrontendEvent, MonitoringException, SqlPerformanceLog

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


def _metric_zombie_workflow_instances(since) -> tuple[float, dict]:
    """Legacy WorkflowInstance 已删除，改为统计僵尸 AgentExecutionRun。"""
    from apps.creation.models import AgentExecutionRun

    threshold = timezone.now() - timedelta(minutes=15)
    qs = AgentExecutionRun.objects.filter(
        status=AgentExecutionRun.STATUS_RUNNING,
        started_at__lt=threshold,
        finished_at__isnull=True,
    )
    return float(qs.count()), {"sample_count": qs.count()}


def _metric_coin_spend_anomaly(since) -> tuple[float, dict]:
    """创作币扣费异常：与昨日同期比较的偏离百分比（绝对值）。"""
    try:
        from apps.billing.models import CoinLedger
    except ImportError:
        return 0.0, {"sample_count": 0, "reason": "billing app unavailable"}
    now = timezone.now()
    # 过去 60min 的扣费合计（delta < 0 表示扣费）
    cur_window_start = now - timedelta(hours=1)
    cur_total = CoinLedger.objects.filter(
        created_at__gte=cur_window_start,
        entry_type=CoinLedger.TYPE_SPEND,
    ).aggregate(total=models.Sum("delta"))["total"] or 0
    # 昨日同时段（昨天的 60min 窗口）
    yesterday_start = cur_window_start - timedelta(days=1)
    yesterday_end = cur_window_start - timedelta(days=1) + timedelta(hours=1)
    yesterday_total = CoinLedger.objects.filter(
        created_at__gte=yesterday_start,
        created_at__lt=yesterday_end,
        entry_type=CoinLedger.TYPE_SPEND,
    ).aggregate(total=models.Sum("delta"))["total"] or 0
    if yesterday_total == 0:
        return 0.0, {"cur_total": float(cur_total), "yesterday_total": 0.0}
    delta = abs(float(cur_total) - float(yesterday_total)) / abs(float(yesterday_total)) * 100
    return round(delta, 2), {
        "cur_total": float(cur_total),
        "yesterday_total": float(yesterday_total),
        "delta_pct": delta,
    }


def _metric_value(rule: AlertRule, since):
    path_filter = Q()
    if rule.path_pattern:
        path_filter = Q(path__icontains=rule.path_pattern)

    if rule.metric_type == AlertRule.MetricType.FRONTEND_ERROR_COUNT:
        qs = FrontendEvent.objects.filter(created_at__gte=since, level__in=["error", "critical"])
        return float(qs.count()), {"sample_count": qs.count()}

    if rule.metric_type == AlertRule.MetricType.BACKEND_ERROR_COUNT:
        qs = MonitoringException.objects.filter(
            created_at__gte=since,
            source=MonitoringException.Source.BACKEND,
        ).filter(path_filter)
        return float(qs.count()), {"sample_count": qs.count()}

    if rule.metric_type == AlertRule.MetricType.BUSINESS_ERROR_COUNT:
        qs = MonitoringException.objects.filter(
            created_at__gte=since,
            source=MonitoringException.Source.BUSINESS,
        ).filter(path_filter)
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
        error_count = qs.filter(extra__business_error=True).count()
        return round(error_count / total * 100, 4), {"sample_count": total, "error_count": error_count}

    if rule.metric_type == AlertRule.MetricType.SLOW_SQL_COUNT:
        qs = SqlPerformanceLog.objects.filter(created_at__gte=since).filter(path_filter)
        return float(qs.count()), {"sample_count": qs.count()}

    if rule.metric_type == AlertRule.MetricType.ZOMBIE_WORKFLOW_INSTANCES:
        return _metric_zombie_workflow_instances(since)

    if rule.metric_type == AlertRule.MetricType.COIN_SPEND_ANOMALY:
        return _metric_coin_spend_anomaly(since)

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
