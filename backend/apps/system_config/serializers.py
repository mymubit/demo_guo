# -*- coding: utf-8 -*-
"""动态配置中心序列化器。"""
from __future__ import annotations

from rest_framework import serializers

from .models import SystemConfigAuditLog, SystemConfigCategory, SystemConfigItem
from .validators import normalize_value, validate_schema

MASKED_VALUE = "******"


class SystemConfigCategorySerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = SystemConfigCategory
        fields = [
            "id",
            "code",
            "name",
            "description",
            "sort_order",
            "is_active",
            "item_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SystemConfigItemSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field="code",
        queryset=SystemConfigCategory.objects.all(),
    )
    category_name = serializers.CharField(source="category.name", read_only=True)
    display_value = serializers.SerializerMethodField()

    class Meta:
        model = SystemConfigItem
        fields = [
            "id",
            "category",
            "category_name",
            "config_key",
            "config_name",
            "value_type",
            "value",
            "display_value",
            "default_value",
            "description",
            "validation_schema",
            "is_active",
            "is_sensitive",
            "is_public",
            "requires_restart",
            "version",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = ["id", "version", "created_at", "updated_at", "deleted_at"]

    def get_display_value(self, obj):
        if obj.is_sensitive:
            return MASKED_VALUE
        return obj.effective_value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_sensitive:
            data["value"] = MASKED_VALUE
            data["default_value"] = MASKED_VALUE
            data["display_value"] = MASKED_VALUE
        return data

    def validate(self, attrs):
        value_type = attrs.get("value_type") or getattr(self.instance, "value_type", None)
        validation_schema = attrs.get(
            "validation_schema",
            getattr(self.instance, "validation_schema", {}) if self.instance else {},
        ) or {}

        if (
            self.instance
            and getattr(self.instance, "is_sensitive", False)
            and attrs.get("value") == MASKED_VALUE
        ):
            attrs.pop("value", None)
        if (
            self.instance
            and getattr(self.instance, "is_sensitive", False)
            and attrs.get("default_value") == MASKED_VALUE
        ):
            attrs.pop("default_value", None)

        if "value" in attrs:
            value = normalize_value(value_type, attrs.get("value"))
            validate_schema(value, validation_schema)
            attrs["value"] = value

        if "default_value" in attrs:
            default_value = normalize_value(value_type, attrs.get("default_value"))
            validate_schema(default_value, validation_schema)
            attrs["default_value"] = default_value

        if attrs.get("is_sensitive") and attrs.get("is_public"):
            raise serializers.ValidationError("敏感配置不能设置为公开读取")

        return attrs

    def update(self, instance, validated_data):
        request = self.context.get("request")
        old_value = instance.effective_value
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.version += 1
        if request and getattr(request.user, "is_authenticated", False):
            instance.updated_by = request.user
        instance.save()

        from .audit import write_audit_log
        from .cache import invalidate_config

        invalidate_config(instance.config_key, instance.category.code)
        write_audit_log(
            config=instance,
            config_key=instance.config_key,
            action=SystemConfigAuditLog.Action.UPDATE,
            old_value=old_value,
            new_value=instance.effective_value,
            request=request,
            change_reason=(request.data or {}).get("change_reason", "") if request else "",
        )
        return instance

    def create(self, validated_data):
        request = self.context.get("request")
        if request and getattr(request.user, "is_authenticated", False):
            validated_data["created_by"] = request.user
            validated_data["updated_by"] = request.user
        instance = super().create(validated_data)

        from .audit import write_audit_log
        from .cache import invalidate_config

        invalidate_config(instance.config_key, instance.category.code)
        write_audit_log(
            config=instance,
            config_key=instance.config_key,
            action=SystemConfigAuditLog.Action.CREATE,
            old_value=None,
            new_value=instance.effective_value,
            request=request,
            change_reason=(request.data or {}).get("change_reason", "") if request else "",
        )
        return instance


class SystemConfigBulkGetSerializer(serializers.Serializer):
    keys = serializers.ListField(
        child=serializers.CharField(max_length=160),
        allow_empty=False,
        max_length=200,
    )


class SystemConfigBulkUpdateSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        max_length=100,
    )
    is_active = serializers.BooleanField(required=False)
    is_public = serializers.BooleanField(required=False)
    change_reason = serializers.CharField(required=False, allow_blank=True, max_length=300)


class SystemConfigAuditLogSerializer(serializers.ModelSerializer):
    operator_name = serializers.SerializerMethodField()

    class Meta:
        model = SystemConfigAuditLog
        fields = [
            "id",
            "config_key",
            "action",
            "old_value",
            "new_value",
            "change_reason",
            "operator_name",
            "ip_address",
            "created_at",
        ]

    def get_operator_name(self, obj):
        user = obj.operator
        if not user:
            return ""
        return getattr(user, "nickname", "") or getattr(user, "phone", "") or str(user.pk)
