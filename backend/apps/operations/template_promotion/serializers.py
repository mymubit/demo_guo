"""模板沉淀序列化器。"""
from __future__ import annotations

from rest_framework import serializers

from apps.operations.template_promotion.models import (
    TemplatePromotion,
    TemplatePromotionLog,
)


class TemplatePromotionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplatePromotionLog
        fields = [
            "id", "promotion", "action", "operator",
            "from_status", "to_status", "note", "created_at",
        ]
        read_only_fields = fields


class TemplatePromotionSerializer(serializers.ModelSerializer):
    logs = TemplatePromotionLogSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    project_title = serializers.CharField(source="project.title", read_only=True, default="")
    source_template_name = serializers.CharField(source="source_template.display_name", read_only=True, default="")
    promoted_pack_name = serializers.CharField(source="promoted_pack.display_name", read_only=True, default="")

    class Meta:
        model = TemplatePromotion
        fields = [
            "id", "project", "project_title",
            "source_template", "source_template_name",
            "promoted_pack", "promoted_pack_name",
            "name", "description", "category", "tags", "cover_url",
            "highlights", "metric_snapshot", "status", "status_display",
            "reviewer", "reviewed_at", "review_note", "published_at",
            "created_by", "created_at", "updated_at", "logs",
        ]
        read_only_fields = [
            "status", "reviewer", "reviewed_at", "review_note",
            "published_at", "promoted_pack", "created_at", "updated_at", "logs",
        ]
