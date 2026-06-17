"""A/B 实验序列化器。"""
from __future__ import annotations

from rest_framework import serializers

from apps.operations.experiment.models import (
    Assignment,
    ConversionLog,
    Experiment,
    ExperimentMetricSnapshot,
    ExposureLog,
    Variant,
)


class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = [
            "id", "experiment", "key", "name", "is_control",
            "weight", "payload", "description", "sort_order",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ExperimentSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    bucket_display = serializers.CharField(source="get_bucket_display", read_only=True)

    class Meta:
        model = Experiment
        fields = [
            "id", "key", "name", "description", "hypothesis",
            "bucket", "bucket_display", "status", "status_display",
            "target_filter", "traffic_allocation", "salt",
            "primary_metric", "secondary_metrics", "min_sample_size",
            "started_at", "ended_at", "conclusion", "winner_variant",
            "operator", "variants", "created_at", "updated_at",
        ]
        read_only_fields = [
            "status", "started_at", "ended_at", "operator",
            "created_at", "updated_at", "variants",
        ]


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "id", "experiment", "user", "anonymous_id",
            "variant_key", "assigned_at",
        ]
        read_only_fields = fields


class ExposureLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExposureLog
        fields = [
            "id", "experiment", "variant", "user", "anonymous_id",
            "surface", "context", "created_at",
        ]
        read_only_fields = fields


class ConversionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversionLog
        fields = [
            "id", "experiment", "variant", "user", "anonymous_id",
            "metric", "value", "surface", "created_at",
        ]
        read_only_fields = fields


class ExperimentMetricSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentMetricSnapshot
        fields = [
            "id", "experiment", "variant", "metric", "snapshot_date",
            "exposure_count", "conversion_count", "conversion_value_sum",
            "extra", "created_at",
        ]
        read_only_fields = fields
