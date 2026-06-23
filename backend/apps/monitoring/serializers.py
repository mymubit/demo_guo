# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from apps.monitoring.models import (
    AlertEvent,
    AlertRule,
    ApiPerformanceLog,
    FrontendEvent,
    MonitoringException,
    SqlPerformanceLog,
)
from apps.monitoring.services.sanitizer import json_size, sanitize_payload


class FrontendEventInSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=FrontendEvent.EventType.choices, source="event_type")
    level = serializers.ChoiceField(choices=["debug", "info", "warning", "error", "critical"], required=False)
    name = serializers.CharField(required=False, allow_blank=True, max_length=120)
    message = serializers.CharField(required=False, allow_blank=True, max_length=4000)
    page_url = serializers.CharField(required=False, allow_blank=True, max_length=1024)
    route = serializers.CharField(required=False, allow_blank=True, max_length=512)
    browser = serializers.CharField(required=False, allow_blank=True, max_length=120)
    os = serializers.CharField(required=False, allow_blank=True, max_length=120)
    user_id = serializers.UUIDField(required=False, allow_null=True)
    session_id = serializers.CharField(required=False, allow_blank=True, max_length=64)
    trace_id = serializers.CharField(required=False, allow_blank=True, max_length=64)
    payload = serializers.JSONField(required=False)
    performance = serializers.JSONField(required=False)
    timestamp = serializers.DateTimeField(required=False, source="created_at")

    def validate(self, attrs):
        max_payload_size = int(getattr(settings, "MONITORING_MAX_PAYLOAD_SIZE", 16 * 1024))
        payload = sanitize_payload(attrs.get("payload"))
        performance = sanitize_payload(attrs.get("performance"))
        if json_size(payload) > max_payload_size:
            raise serializers.ValidationError("payload 过大")
        if json_size(performance) > max_payload_size:
            raise serializers.ValidationError("performance 过大")
        attrs["payload"] = payload
        attrs["performance"] = performance
        attrs["created_at"] = attrs.get("created_at") or timezone.now()
        attrs["level"] = attrs.get("level") or "info"
        return attrs


class FrontendEventBatchSerializer(serializers.Serializer):
    events = FrontendEventInSerializer(many=True)

    def validate_events(self, value):
        max_batch = int(getattr(settings, "MONITORING_MAX_BATCH_SIZE", 50))
        if len(value) > max_batch:
            raise serializers.ValidationError(f"单批最多允许 {max_batch} 条")
        return value


class MonitoringExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitoringException
        fields = "__all__"


class ApiPerformanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiPerformanceLog
        fields = "__all__"


class FrontendEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrontendEvent
        fields = "__all__"


class SqlPerformanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SqlPerformanceLog
        fields = "__all__"


class AlertRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRule
        fields = "__all__"
        read_only_fields = ("id", "created_by", "last_triggered_at", "created_at", "updated_at")


class AlertEventSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source="rule.name", read_only=True)

    class Meta:
        model = AlertEvent
        fields = "__all__"
