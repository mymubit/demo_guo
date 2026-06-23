# -*- coding: utf-8 -*-
from django.contrib import admin

from apps.monitoring.models import (
    AlertEvent,
    AlertRule,
    ApiPerformanceLog,
    FrontendEvent,
    MonitoringException,
    ServiceHealthSnapshot,
    SqlPerformanceLog,
)


@admin.register(MonitoringException)
class MonitoringExceptionAdmin(admin.ModelAdmin):
    list_display = ("source", "level", "exception_type", "path", "status_code", "created_at")
    list_filter = ("source", "level", "status_code")
    search_fields = ("message", "path", "trace_id", "fingerprint")
    readonly_fields = [field.name for field in MonitoringException._meta.fields]


@admin.register(ApiPerformanceLog)
class ApiPerformanceLogAdmin(admin.ModelAdmin):
    list_display = ("method", "path", "status_code", "duration_ms", "created_at")
    list_filter = ("method", "status_code")
    search_fields = ("path", "trace_id")
    readonly_fields = [field.name for field in ApiPerformanceLog._meta.fields]


@admin.register(FrontendEvent)
class FrontendEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "level", "name", "route", "created_at")
    list_filter = ("event_type", "level")
    search_fields = ("name", "message", "route", "trace_id", "session_id")
    readonly_fields = [field.name for field in FrontendEvent._meta.fields]


@admin.register(SqlPerformanceLog)
class SqlPerformanceLogAdmin(admin.ModelAdmin):
    list_display = ("method", "path", "duration_ms", "sql_hash", "created_at")
    search_fields = ("path", "sql_hash", "trace_id")
    readonly_fields = [field.name for field in SqlPerformanceLog._meta.fields]


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "metric_type", "threshold", "window_minutes", "level", "is_enabled")
    list_filter = ("metric_type", "level", "is_enabled")
    search_fields = ("name", "path_pattern")


@admin.register(AlertEvent)
class AlertEventAdmin(admin.ModelAdmin):
    list_display = ("rule", "metric_type", "level", "value", "threshold", "status", "triggered_at")
    list_filter = ("metric_type", "level", "status")
    readonly_fields = [field.name for field in AlertEvent._meta.fields]


@admin.register(ServiceHealthSnapshot)
class ServiceHealthSnapshotAdmin(admin.ModelAdmin):
    list_display = ("service_name", "status", "checked_at")
    list_filter = ("service_name", "status")
    readonly_fields = [field.name for field in ServiceHealthSnapshot._meta.fields]
