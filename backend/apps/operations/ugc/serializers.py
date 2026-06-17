"""UGC 模板市场序列化器。"""
from __future__ import annotations

from rest_framework import serializers

from apps.operations.ugc.models import (
    UserTemplate,
    UserTemplateCollection,
    UserTemplateRating,
)


class UserTemplateRatingSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default="")

    class Meta:
        model = UserTemplateRating
        fields = ["id", "template", "user", "username", "score", "comment", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "username", "created_at", "updated_at"]


class UserTemplateCollectionSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True, default="")
    template_cover = serializers.CharField(source="template.cover_url", read_only=True, default="")
    template_slug = serializers.CharField(source="template.slug", read_only=True, default="")

    class Meta:
        model = UserTemplateCollection
        fields = [
            "id", "template", "template_name", "template_cover", "template_slug",
            "collection_name", "created_at",
        ]
        read_only_fields = fields


class UserTemplateListSerializer(serializers.ModelSerializer):
    """前台列表 / 搜索。"""

    author_name = serializers.CharField(source="author.username", read_only=True, default="")
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = UserTemplate
        fields = [
            "id", "slug", "name", "description", "category", "tags", "cover_url",
            "author", "author_name",
            "status", "status_display",
            "downloads_count", "uses_count", "rating_count", "rating_avg",
            "collection_count", "is_featured", "sort_weight",
            "published_at", "created_at", "updated_at",
        ]
        read_only_fields = fields


class UserTemplateDetailSerializer(UserTemplateListSerializer):
    """详情：包含 pack_snapshot。"""

    ratings = UserTemplateRatingSerializer(many=True, read_only=True)

    class Meta(UserTemplateListSerializer.Meta):
        fields = UserTemplateListSerializer.Meta.fields + ["pack_snapshot", "source_pack", "ratings"]
        read_only_fields = fields


class UserTemplateCreateSerializer(serializers.ModelSerializer):
    """创作者发布。"""

    class Meta:
        model = UserTemplate
        fields = [
            "name", "description", "category", "tags", "cover_url",
            "pack_snapshot", "source_pack",
        ]
