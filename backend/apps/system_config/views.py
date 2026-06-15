# -*- coding: utf-8 -*-
"""动态配置中心 API。"""
from __future__ import annotations

from django.db import transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.common.permissions import IsAdminUser
from apps.console.responses import api_fail, api_ok

from .audit import write_audit_log
from .cache import clear_all_config_cache, current_version, invalidate_config
from .models import SystemConfigAuditLog, SystemConfigCategory, SystemConfigItem
from .serializers import (
    SystemConfigAuditLogSerializer,
    SystemConfigBulkGetSerializer,
    SystemConfigBulkUpdateSerializer,
    SystemConfigCategorySerializer,
    SystemConfigItemSerializer,
)
from .services import SystemConfigService


def _paginate(request, queryset, serializer_class, *, context=None):
    paginator = StandardPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context=context or {"request": request})
    return paginator.get_paginated_response(serializer.data)


class AdminSystemConfigCategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        queryset = (
            SystemConfigCategory.objects.annotate(
                item_count=Count("items", filter=Q(items__deleted_at__isnull=True))
            )
            .all()
            .order_by("sort_order", "code")
        )
        serializer = SystemConfigCategorySerializer(queryset, many=True)
        return api_ok(serializer.data)

    def post(self, request):
        serializer = SystemConfigCategorySerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        row = serializer.save()
        return api_ok(SystemConfigCategorySerializer(row).data, message="分类已创建", http_status=status.HTTP_201_CREATED)


class AdminSystemConfigCategoryDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self, category_id):
        return SystemConfigCategory.objects.filter(pk=category_id).first()

    def patch(self, request, category_id):
        row = self.get_object(category_id)
        if row is None:
            return api_fail("配置分类不存在", code=404)
        serializer = SystemConfigCategorySerializer(row, data=request.data or {}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_ok(serializer.data, message="分类已更新")

    def put(self, request, category_id):
        return self.patch(request, category_id)

    def delete(self, request, category_id):
        row = self.get_object(category_id)
        if row is None:
            return api_fail("配置分类不存在", code=404)
        if row.items.filter(deleted_at__isnull=True).exists():
            row.is_active = False
            row.save(update_fields=["is_active", "updated_at"])
            return api_ok({"id": str(row.id), "is_active": row.is_active}, message="分类下存在配置项，已禁用")
        row.delete()
        return api_ok(None, message="分类已删除")


class AdminSystemConfigListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self, request):
        queryset = SystemConfigItem.objects.select_related("category").filter(deleted_at__isnull=True)
        keyword = (request.query_params.get("keyword") or "").strip()
        category = (request.query_params.get("category") or "").strip()
        value_type = (request.query_params.get("value_type") or "").strip()
        is_active = (request.query_params.get("is_active") or "").strip().lower()
        is_public = (request.query_params.get("is_public") or "").strip().lower()

        if keyword:
            queryset = queryset.filter(
                Q(config_key__icontains=keyword)
                | Q(config_name__icontains=keyword)
                | Q(description__icontains=keyword)
            )
        if category:
            queryset = queryset.filter(category__code=category)
        if value_type:
            queryset = queryset.filter(value_type=value_type)
        if is_active in ("true", "false"):
            queryset = queryset.filter(is_active=is_active == "true")
        if is_public in ("true", "false"):
            queryset = queryset.filter(is_public=is_public == "true")

        return queryset.order_by("category__sort_order", "config_key")

    def get(self, request):
        return _paginate(
            request,
            self.get_queryset(request),
            SystemConfigItemSerializer,
            context={"request": request},
        )

    def post(self, request):
        serializer = SystemConfigItemSerializer(data=request.data or {}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        row = serializer.save()
        return api_ok(SystemConfigItemSerializer(row, context={"request": request}).data, message="配置已创建", http_status=status.HTTP_201_CREATED)


class AdminSystemConfigDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self, config_id):
        return SystemConfigItem.objects.select_related("category").filter(pk=config_id, deleted_at__isnull=True).first()

    def get(self, request, config_id):
        row = self.get_object(config_id)
        if row is None:
            return api_fail("配置项不存在", code=404)
        return api_ok(SystemConfigItemSerializer(row, context={"request": request}).data)

    def patch(self, request, config_id):
        row = self.get_object(config_id)
        if row is None:
            return api_fail("配置项不存在", code=404)
        serializer = SystemConfigItemSerializer(row, data=request.data or {}, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_ok(serializer.data, message="配置已更新")

    def put(self, request, config_id):
        return self.patch(request, config_id)

    def delete(self, request, config_id):
        row = self.get_object(config_id)
        if row is None:
            return api_fail("配置项不存在", code=404)
        old_value = row.effective_value
        row.soft_delete(request.user)
        invalidate_config(row.config_key, row.category.code)
        write_audit_log(
            config=row,
            config_key=row.config_key,
            action=SystemConfigAuditLog.Action.DELETE,
            old_value=old_value,
            new_value=None,
            request=request,
            change_reason=(request.data or {}).get("change_reason", ""),
        )
        return api_ok(None, message="配置已删除")


class AdminSystemConfigToggleView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, config_id):
        row = SystemConfigItem.objects.select_related("category").filter(pk=config_id, deleted_at__isnull=True).first()
        if row is None:
            return api_fail("配置项不存在", code=404)
        old_value = {"is_active": row.is_active}
        row.is_active = not row.is_active
        row.version += 1
        row.updated_by = request.user
        row.save(update_fields=["is_active", "version", "updated_by", "updated_at"])
        invalidate_config(row.config_key, row.category.code)
        write_audit_log(
            config=row,
            config_key=row.config_key,
            action=SystemConfigAuditLog.Action.TOGGLE,
            old_value=old_value,
            new_value={"is_active": row.is_active},
            request=request,
            change_reason=(request.data or {}).get("change_reason", ""),
        )
        return api_ok(SystemConfigItemSerializer(row, context={"request": request}).data, message="配置状态已更新")


class AdminSystemConfigBulkUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = SystemConfigBulkUpdateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ids = data["ids"]
        fields = {}
        if "is_active" in data:
            fields["is_active"] = data["is_active"]
        if "is_public" in data:
            fields["is_public"] = data["is_public"]
        if not fields:
            return api_fail("未提供可批量更新的字段")

        rows = list(SystemConfigItem.objects.select_related("category").filter(id__in=ids, deleted_at__isnull=True))
        with transaction.atomic():
            for row in rows:
                old_value = {key: getattr(row, key) for key in fields}
                for key, value in fields.items():
                    setattr(row, key, value)
                row.version += 1
                row.updated_by = request.user
                row.save(update_fields=[*fields.keys(), "version", "updated_by", "updated_at"])
                invalidate_config(row.config_key, row.category.code)
                write_audit_log(
                    config=row,
                    config_key=row.config_key,
                    action=SystemConfigAuditLog.Action.UPDATE,
                    old_value=old_value,
                    new_value=fields,
                    request=request,
                    change_reason=data.get("change_reason", ""),
                )
        return api_ok({"updated": len(rows)}, message="批量更新完成")


class AdminSystemConfigRefreshCacheView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        clear_all_config_cache()
        write_audit_log(
            config=None,
            config_key="*",
            action=SystemConfigAuditLog.Action.REFRESH_CACHE,
            request=request,
            change_reason=(request.data or {}).get("change_reason", "手动刷新配置缓存"),
        )
        return api_ok({"version": current_version()}, message="配置缓存已刷新")


class AdminSystemConfigAuditLogView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        queryset = SystemConfigAuditLog.objects.select_related("operator").all()
        key = (request.query_params.get("config_key") or "").strip()
        if key:
            queryset = queryset.filter(config_key=key)
        return _paginate(request, queryset, SystemConfigAuditLogSerializer, context={"request": request})


class PublicSystemConfigView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        payload = SystemConfigService.public_config_payload()
        return api_ok({**payload, "version": current_version()})


class PublicSystemConfigBatchView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SystemConfigBulkGetSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        values = SystemConfigService.get_many(serializer.validated_data["keys"], public_only=True)
        return api_ok({"values": values, "version": current_version()})


class PublicSystemConfigDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, config_key):
        row = (
            SystemConfigItem.objects.select_related("category")
            .filter(
                config_key=config_key,
                is_active=True,
                is_public=True,
                is_sensitive=False,
                deleted_at__isnull=True,
            )
            .first()
        )
        if row is None:
            return api_fail("配置项不存在或不可公开读取", code=404)
        return api_ok({"key": row.config_key, "value": row.effective_value, "version": row.version})
