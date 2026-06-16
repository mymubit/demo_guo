import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class MonitorLevel(models.TextChoices):
    DEBUG = "debug", _("DEBUG")
    INFO = "info", _("INFO")
    WARNING = "warning", _("WARNING")
    ERROR = "error", _("ERROR")
    CRITICAL = "critical", _("CRITICAL")


class MonitoringException(models.Model):
    class Source(models.TextChoices):
        FRONTEND = "frontend", _("前端")
        BACKEND = "backend", _("后端")
        BUSINESS = "business", _("业务 API")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=16, choices=Source.choices, db_index=True)
    level = models.CharField(max_length=16, choices=MonitorLevel.choices, default=MonitorLevel.ERROR, db_index=True)
    exception_type = models.CharField(max_length=120, blank=True, default="", db_index=True)
    message = models.TextField(blank=True, default="")
    stack = models.TextField(blank=True, default="")
    path = models.CharField(max_length=512, blank=True, default="", db_index=True)
    method = models.CharField(max_length=12, blank=True, default="", db_index=True)
    status_code = models.IntegerField(null=True, blank=True, db_index=True)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")
    trace_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    fingerprint = models.CharField(max_length=64, blank=True, default="", db_index=True)
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "sf_monitoring_exception"
        verbose_name = "异常记录"
        verbose_name_plural = "异常记录"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "-created_at"]),
            models.Index(fields=["level", "-created_at"]),
            models.Index(fields=["path", "-created_at"]),
            models.Index(fields=["fingerprint", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.source}:{self.exception_type}:{self.created_at:%Y-%m-%d %H:%M:%S}"


class ApiPerformanceLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    path = models.CharField(max_length=512, db_index=True)
    method = models.CharField(max_length=12, db_index=True)
    status_code = models.IntegerField(null=True, blank=True, db_index=True)
    duration_ms = models.PositiveIntegerField(db_index=True)
    query_count = models.PositiveIntegerField(default=0)
    slow_sql_count = models.PositiveIntegerField(default=0)
    request_size = models.PositiveIntegerField(default=0)
    response_size = models.PositiveIntegerField(default=0)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")
    trace_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "sf_api_performance_log"
        verbose_name = "接口性能日志"
        verbose_name_plural = "接口性能日志"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["path", "-created_at"]),
            models.Index(fields=["status_code", "-created_at"]),
            models.Index(fields=["duration_ms", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.method} {self.path} {self.duration_ms}ms"


class FrontendEvent(models.Model):
    class EventType(models.TextChoices):
        JS_ERROR = "js_error", _("JS 错误")
        RESOURCE_ERROR = "resource_error", _("资源加载错误")
        PROMISE_ERROR = "promise_error", _("Promise 错误")
        API_ERROR = "api_error", _("接口异常")
        API_BUSINESS_ERROR = "api_business_error", _("业务接口失败")
        PERFORMANCE = "performance", _("页面性能")
        PAGE_VIEW = "page_view", _("页面访问")
        PAGE_LEAVE = "page_leave", _("页面离开")
        USER_ACTION = "user_action", _("用户行为")
        CUSTOM = "custom", _("自定义事件")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=32, choices=EventType.choices, db_index=True)
    level = models.CharField(max_length=16, choices=MonitorLevel.choices, default=MonitorLevel.INFO, db_index=True)
    name = models.CharField(max_length=120, blank=True, default="", db_index=True)
    message = models.TextField(blank=True, default="")
    page_url = models.CharField(max_length=1024, blank=True, default="")
    route = models.CharField(max_length=512, blank=True, default="", db_index=True)
    browser = models.CharField(max_length=120, blank=True, default="")
    os = models.CharField(max_length=120, blank=True, default="")
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    session_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    trace_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    performance = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "sf_frontend_event"
        verbose_name = "前端监控事件"
        verbose_name_plural = "前端监控事件"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "-created_at"]),
            models.Index(fields=["level", "-created_at"]),
            models.Index(fields=["route", "-created_at"]),
            models.Index(fields=["session_id", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type}:{self.name or self.route}"


class SqlPerformanceLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    path = models.CharField(max_length=512, blank=True, default="", db_index=True)
    method = models.CharField(max_length=12, blank=True, default="", db_index=True)
    sql = models.TextField(blank=True, default="")
    sql_hash = models.CharField(max_length=64, db_index=True)
    duration_ms = models.PositiveIntegerField(db_index=True)
    trace_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    stack = models.TextField(blank=True, default="")
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "sf_sql_performance_log"
        verbose_name = "慢 SQL 日志"
        verbose_name_plural = "慢 SQL 日志"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sql_hash", "-created_at"]),
            models.Index(fields=["duration_ms", "-created_at"]),
            models.Index(fields=["path", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.duration_ms}ms {self.sql_hash}"


class AlertRule(models.Model):
    class MetricType(models.TextChoices):
        FRONTEND_ERROR_COUNT = "frontend_error_count", _("前端异常数")
        BACKEND_ERROR_COUNT = "backend_error_count", _("后端异常数")
        BUSINESS_ERROR_COUNT = "business_error_count", _("业务 API 错误数")
        API_AVG_DURATION = "api_avg_duration", _("接口平均耗时")
        API_ERROR_RATE = "api_error_rate", _("接口错误率")
        SLOW_SQL_COUNT = "slow_sql_count", _("慢 SQL 数")

    class Comparator(models.TextChoices):
        GT = "gt", _("大于")
        GTE = "gte", _("大于等于")
        LT = "lt", _("小于")
        LTE = "lte", _("小于等于")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, db_index=True)
    metric_type = models.CharField(max_length=64, choices=MetricType.choices, db_index=True)
    comparator = models.CharField(max_length=8, choices=Comparator.choices, default=Comparator.GTE)
    threshold = models.FloatField()
    window_minutes = models.PositiveIntegerField(default=5)
    level = models.CharField(max_length=16, choices=MonitorLevel.choices, default=MonitorLevel.WARNING)
    path_pattern = models.CharField(max_length=256, blank=True, default="")
    channels = models.JSONField(default=list, blank=True)
    cooldown_minutes = models.PositiveIntegerField(default=10)
    is_enabled = models.BooleanField(default=True, db_index=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="monitoring_alert_rules",
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sf_alert_rule"
        verbose_name = "告警规则"
        verbose_name_plural = "告警规则"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["metric_type", "is_enabled"]),
            models.Index(fields=["is_enabled", "-created_at"]),
        ]

    def __str__(self):
        return self.name


class AlertEvent(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", _("待处理")
        ACKED = "acked", _("已确认")
        RESOLVED = "resolved", _("已恢复")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name="events")
    metric_type = models.CharField(max_length=64, db_index=True)
    level = models.CharField(max_length=16, choices=MonitorLevel.choices, db_index=True)
    value = models.FloatField()
    threshold = models.FloatField()
    message = models.CharField(max_length=512)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True)
    snapshot = models.JSONField(default=dict, blank=True)
    triggered_at = models.DateTimeField(default=timezone.now, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "sf_alert_event"
        verbose_name = "告警事件"
        verbose_name_plural = "告警事件"
        ordering = ["-triggered_at"]
        indexes = [
            models.Index(fields=["metric_type", "-triggered_at"]),
            models.Index(fields=["status", "-triggered_at"]),
            models.Index(fields=["rule", "-triggered_at"]),
        ]

    def __str__(self):
        return self.message


class ServiceHealthSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_name = models.CharField(max_length=80, db_index=True)
    status = models.CharField(max_length=32, default="ok", db_index=True)
    metrics = models.JSONField(default=dict, blank=True)
    checked_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "sf_service_health_snapshot"
        verbose_name = "服务健康快照"
        verbose_name_plural = "服务健康快照"
        ordering = ["-checked_at"]
        indexes = [
            models.Index(fields=["service_name", "-checked_at"]),
            models.Index(fields=["status", "-checked_at"]),
        ]

    def __str__(self):
        return f"{self.service_name}:{self.status}"
