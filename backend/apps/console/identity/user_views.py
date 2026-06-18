# -*- coding: utf-8 -*-
"""后台 API — 用户中心 — 用户管理"""
import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.common.pagination import StandardPagination
from apps.console.responses import (
    CACHE_KEY_DASHBOARD,
    CACHE_KEY_DASHBOARD_LEGACY,
    CACHE_KEY_STATS,
    CACHE_KEY_SKILL_CONFIG_PREFIX,
    CACHE_TTL,
    DEFAULT_CONFIG_KEYS,
    api_fail,
    _is_sensitive_key,
    api_ok,
    _random_password)

from apps.users.models import User
from apps.membership.models import UserMembership
from apps.console.serializers import (
    AdminUserSerializer,
    ResetPasswordResultSerializer,
    ResetPasswordSerializer,
    UserToggleActiveResultSerializer,
)


# ============================================================
# 用户管理
# ============================================================

class UserManagementViewSet(viewsets.GenericViewSet):
    """用户管理
    - list: GET /api/admin/users/?keyword=&is_active=&member=active|free&page=&page_size=
    - toggle_active: POST /api/admin/users/<id>/toggle_active/
    - reset_password: POST /api/admin/users/<id>/reset_password/
    - 排序：?ordering=-created_at
    """

    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminUserSerializer
    pagination_class = StandardPagination
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
    lookup_field = "pk"

    def _base_queryset(self):
        from django.db.models import Prefetch
        from apps.membership.models import UserMembership as _UserMembership

        qs = User.objects.prefetch_related(
            Prefetch(
                "memberships",
                queryset=_UserMembership.objects.select_related("plan").filter(
                    is_active=True, end_at__gt=timezone.now()
                ),
                to_attr="_prefetched_active_memberships",
            )
        ).order_by("-created_at")
        keyword = self.request.query_params.get("keyword", "").strip()
        is_active = self.request.query_params.get("is_active")
        if keyword:
            qs = qs.filter(
                Q(nickname__icontains=keyword)
                | Q(phone__icontains=keyword)
                | Q(email__icontains=keyword)
            )
        if is_active in ("true", "1", "True"):
            qs = qs.filter(is_active=True)
        elif is_active in ("false", "0", "False"):
            qs = qs.filter(is_active=False)
        member = self.request.query_params.get("member", "").strip()
        if member == "active":
            qs = qs.filter(
                id__in=UserMembership.objects.filter(
                    is_active=True, end_at__gt=timezone.now()
                ).values("user_id")
            )
        elif member == "free":
            qs = qs.exclude(
                id__in=UserMembership.objects.filter(
                    is_active=True, end_at__gt=timezone.now()
                ).values("user_id")
            )
        return qs

    def list(self, request, *args, **kwargs):
        qs = self._base_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return api_ok(serializer.data)

    @action(detail=True, methods=["post"], url_path="toggle_active")
    def toggle_active(self, request, pk=None):
        """启用/禁用用户（切换 is_active）"""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return api_fail("用户不存在")
        # 不允许禁用自己或其他超级管理员（自我保护）
        if user == request.user or user.is_superuser:
            return api_fail("不能禁用超级管理员或当前账号")
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        # 清除该用户相关缓存（登录态等）
        cache.delete_pattern(f"auth:user:{user.pk}:*")
        data = {
            "user_id": user.pk,
            "is_active": user.is_active,
            "message": "已启用" if user.is_active else "已禁用",
        }
        serializer = UserToggleActiveResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 清除 dashboard 缓存
        cache.delete(CACHE_KEY_DASHBOARD)
        return api_ok(serializer.validated_data)

    @action(detail=True, methods=["get"], url_path="recent_projects")
    def recent_projects(self, request, pk=None):
        """用户最近创作项目摘要（运营穿透）。"""
        from apps.creation.admin_status import resolve_admin_status
        from apps.creation.models import Project

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return api_fail("用户不存在")
        rows = []
        for project in Project.objects.filter(user=user).order_by("-updated_at")[:12]:
            status, status_text = resolve_admin_status(project)
            rows.append(
                {
                    "project_id": str(project.id),
                    "title": (project.title or project.theme or "未命名")[:200],
                    "status": status,
                    "status_text": status_text,
                    "pipeline_mode": project.pipeline_mode,
                    "updated_at": project.updated_at.isoformat() if project.updated_at else "",
                }
            )
        return api_ok({"items": rows})

    @action(detail=True, methods=["post"], url_path="reset_password")
    def reset_password(self, request, pk=None):
        """重置密码：接受 new_password；为空则由后端自动生成 12 位随机密码"""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return api_fail("用户不存在")

        input_ser = ResetPasswordSerializer(data=request.data or {})
        input_ser.is_valid(raise_exception=True)
        new_password = input_ser.validated_data.get("new_password") or _random_password(12)

        user.password = make_password(new_password)
        user.save(update_fields=["password"])

        data = {
            "user_id": user.pk,
            "new_password": new_password,
            "message": "密码已重置",
        }
        serializer = ResetPasswordResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return api_ok(serializer.validated_data)
