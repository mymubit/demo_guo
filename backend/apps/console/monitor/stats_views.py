# -*- coding: utf-8 -*-
"""后台 API — 监控中心 — 统计与系统"""
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
from apps.membership.models import MembershipPlan, UserMembership
from apps.orders.models import Order
from apps.console.serializers import (
    CacheClearResultSerializer,
    StatsSummarySerializer,
    SystemSettingsSerializer,
)
from apps.system_config.services import get_config


# ============================================================
# 统计总览
# ============================================================

class StatsSummaryView(APIView):
    """统计总览（比 dashboard 更细粒度的统计数据）

    包含订单分状态统计、会员分套餐统计等；缓存 5 分钟
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def _compute(self):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        total_users = User.objects.count()
        today_new_users = User.objects.filter(created_at__gte=today_start).count()
        total_members = UserMembership.objects.filter(
            is_active=True, end_at__gt=now
        ).count()

        orders = Order.objects
        total_orders = orders.count()
        paid_orders = orders.filter(status=Order.STATUS_PAID).count()
        pending_orders = orders.filter(status=Order.STATUS_PENDING).count()
        refunded_orders = orders.filter(status=Order.STATUS_REFUNDED).count()
        total_revenue = orders.filter(status=Order.STATUS_PAID).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")

        # 创作数
        total_creations = 0
        today_creations = 0
        try:
            from django.apps import apps as django_apps
            for app_label, model_name in [("creation", "Script"), ("creation", "Creation")]:
                model_cls = django_apps.get_model(app_label, model_name, require_ready=False)
                total_creations = model_cls.objects.count()
                if hasattr(model_cls, "created_at"):
                    today_creations = model_cls.objects.filter(
                        created_at__gte=today_start
                    ).count()
                break
        except Exception:
            total_creations = 0
            today_creations = 0

        summary = {
            "users": {
                "total_users": total_users,
                "today_new_users": today_new_users,
                "total_members": total_members,
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "total_creations": total_creations,
                "today_creations": today_creations,
            },
            "orders": {
                "total": total_orders,
                "paid": paid_orders,
                "pending": pending_orders,
                "refunded": refunded_orders,
                "total_revenue": str(total_revenue),
            },
            "members": {
                "total_active": total_members,
                "plans": [
                    {
                        "plan_id": p.id,
                        "plan_name": p.name,
                        "member_count": UserMembership.objects.filter(
                            plan=p, is_active=True, end_at__gt=now
                        ).count(),
                    }
                    for p in MembershipPlan.objects.all()
                ],
            },
            "creations": {
                "total": total_creations,
                "today": today_creations,
            },
            "cache_hit_rate": 0.0,
        }
        return summary

    def get(self, request):
        data = cache.get(CACHE_KEY_STATS)
        if not data:
            data = self._compute()
            cache.set(CACHE_KEY_STATS, data, CACHE_TTL)
        serializer = StatsSummarySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return api_ok(serializer.validated_data)


# ============================================================
# 系统设置与缓存
# ============================================================

class SystemSettingsView(APIView):
    """系统设置（只读快照）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        data = {
            "site_name": get_config("system.site_name", getattr(settings, "SITE_NAME", "ScriptForge 短剧创作平台")),
            "support_email": get_config("system.support_email", getattr(settings, "SUPPORT_EMAIL", "support@scriptforge.local")),
            "cache_backend": getattr(settings, "CACHES", {}).get("default", {}).get("BACKEND", ""),
            "time_zone": getattr(settings, "TIME_ZONE", "Asia/Shanghai"),
            "debug_mode": bool(getattr(settings, "DEBUG", False)),
            "api_rate_limit_per_hour": int(
                getattr(settings, "DEFAULT_THROTTLE_RATES", {}).get("user", "1000/hour").split("/")[0]
            ),
        }
        serializer = SystemSettingsSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return api_ok(serializer.validated_data)


class CacheClearView(APIView):
    """清除缓存（admin 命名空间 + dashboard/skill 相关 key）"""

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        # 精确清除我们管理的 key；不直接调用 cache.clear() 以免误伤用户登录态
        cleared = 0
        targets = [
            CACHE_KEY_DASHBOARD,
            CACHE_KEY_DASHBOARD_LEGACY,
            CACHE_KEY_STATS,
        ]
        for k in targets:
            if cache.delete(k):
                cleared += 1
        # 前缀匹配
        try:
            # cache.delete_pattern 由 django-redis 提供；若后端不支持则静默跳过
            cleared += cache.delete_pattern(CACHE_KEY_SKILL_CONFIG_PREFIX + "*") or 0
            cleared += cache.delete_pattern("admin:*") or 0
            cleared += cache.delete_pattern("skill:config:*") or 0
        except Exception:
            pass

        data = {
            "success": True,
            "message": "缓存已清除",
            "cleared_keys": int(cleared),
        }
        serializer = CacheClearResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return api_ok(serializer.validated_data)
