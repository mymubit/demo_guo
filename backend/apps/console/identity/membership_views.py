# -*- coding: utf-8 -*-
"""后台 API — 用户中心 — 会员与卡密"""
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

from apps.membership.models import MembershipPlan, PromoCode, UserMembership
from apps.console.serializers import (
    MembershipPlanCreateUpdateSerializer,
    MembershipPlanSerializer,
    PromoCodeGenerateSerializer,
    PromoCodeSerializer,
)


# ============================================================
# 会员管理
# ============================================================

class MembershipPlanViewSet(viewsets.ModelViewSet):
    """会员套餐管理：列表 / 新增 / 更新
    - 软删除（实际仅禁用）可以通过 PUT is_active=False 实现
    - 过滤：?is_active=true
    - 排序：?ordering=sort_order,-created_at
    """

    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardPagination
    filterset_fields = ["is_active"]
    search_fields = ["name"]
    ordering_fields = ["sort_order", "created_at", "price"]
    ordering = ["sort_order", "-created_at"]

    def get_queryset(self):
        return MembershipPlan.objects.all().order_by("sort_order", "-created_at")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return MembershipPlanCreateUpdateSerializer
        return MembershipPlanSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return api_ok(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        cache.delete(CACHE_KEY_DASHBOARD)
        return api_ok(serializer.data, message="套餐已创建", http_status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.get("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        cache.delete(CACHE_KEY_DASHBOARD)
        return api_ok(serializer.data, message="套餐已更新")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if UserMembership.objects.filter(plan=instance).exists():
            return api_fail("已有会员使用此套餐，无法删除；可将 is_active 设置为 False 以停用")
        instance.delete()
        cache.delete(CACHE_KEY_DASHBOARD)
        return api_ok(None, message="套餐已删除")


class PromoCodeListView(APIView):
    """卡密列表（最近生成的兑换码）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        limit = min(int(request.query_params.get("limit", "50")), 200)
        qs = (
            PromoCode.objects.select_related("plan")
            .order_by("-created_at")[:limit]
        )
        serializer = PromoCodeSerializer(qs, many=True)
        return api_ok(serializer.data)


class PromoCodeGenerateView(APIView):
    """批量生成卡密"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request):
        input_ser = PromoCodeGenerateSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        data = input_ser.validated_data
        try:
            plan = MembershipPlan.objects.get(pk=data["plan_id"])
        except MembershipPlan.DoesNotExist:
            return api_fail("套餐不存在")

        count = int(data["count"])
        valid_days = int(data["valid_days"])
        max_uses = int(data["max_uses_per_code"])
        expires_at = timezone.now() + timedelta(days=valid_days)

        created = []
        existing_codes = set(
            PromoCode.objects.values_list("code", flat=True)
        )
        for _ in range(count):
            while True:
                code = secrets.token_urlsafe(8).replace("-", "").replace("_", "").upper()[:16]
                # 确保唯一
                if code not in existing_codes:
                    existing_codes.add(code)
                    break
            created.append(
                PromoCode(
                    code=code,
                    plan=plan,
                    max_uses=max_uses,
                    used_count=0,
                    expires_at=expires_at,
                    is_active=True,
                )
            )
        PromoCode.objects.bulk_create(created, batch_size=200)

        codes_ser = PromoCodeSerializer(created, many=True)
        result = {
            "plan_id": plan.pk,
            "plan_name": plan.name,
            "generated_count": len(created),
            "codes": codes_ser.data,
        }
        return api_ok(result, message=f"已生成 {len(created)} 张卡密")
