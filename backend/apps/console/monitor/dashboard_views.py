# -*- coding: utf-8 -*-
"""后台 API — 监控中心 — Dashboard"""
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
    _random_password,
)

from apps.users.models import User
from apps.membership.models import MembershipPlan, UserMembership
from apps.orders.models import Order
from apps.billing.models import CoinLedger, UserWallet
from apps.billing.services import BillingService
from apps.console.serializers import DashboardDataSerializer


# ============================================================
# Dashboard
# ============================================================

def build_commerce_ops_alerts() -> dict:
    """Dashboard / 用户与交易待办计数。"""
    return {
        "pending_orders": Order.objects.filter(status=Order.STATUS_PENDING).count(),
        "inactive_users": User.objects.filter(is_active=False, is_superuser=False).count(),
    }


class DashboardView(APIView):
    """管理后台首页仪表盘

    核心指标 + 图表数据，缓存 5 分钟
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    @staticmethod
    def _paid_orders_in_range(day_start, day_end):
        return Order.objects.filter(status=Order.STATUS_PAID).filter(
            Q(paid_at__gte=day_start, paid_at__lt=day_end)
            | Q(paid_at__isnull=True, created_at__gte=day_start, created_at__lt=day_end)
        )

    @staticmethod
    def _compute_dashboard():
        """计算仪表盘数据（未命中缓存时调用）"""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # ---- 核心指标 ----
        total_users = User.objects.count()
        today_new_users = User.objects.filter(created_at__gte=today_start).count()
        total_members = (
            UserMembership.objects.filter(is_active=True, end_at__gt=now).count()
        )
        total_orders = Order.objects.count()
        paid_orders = Order.objects.filter(status=Order.STATUS_PAID)
        total_revenue = paid_orders.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        membership_revenue_total = paid_orders.filter(
            order_type=Order.TYPE_MEMBERSHIP
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        recharge_revenue_total = paid_orders.filter(
            order_type=Order.TYPE_RECHARGE
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        today_paid = DashboardView._paid_orders_in_range(today_start, today_start + timedelta(days=1))
        today_revenue = today_paid.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        today_membership_yuan = today_paid.filter(order_type=Order.TYPE_MEMBERSHIP).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")
        today_recharge_yuan = today_paid.filter(order_type=Order.TYPE_RECHARGE).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")

        spend_ledgers = CoinLedger.objects.filter(entry_type=CoinLedger.TYPE_SPEND)
        total_coins_spent = int(
            abs(spend_ledgers.aggregate(total=Sum("delta"))["total"] or 0)
        )
        today_coins_spent = int(
            abs(
                spend_ledgers.filter(created_at__gte=today_start).aggregate(total=Sum("delta"))[
                    "total"
                ]
                or 0
            )
        )
        today_skill_calls = spend_ledgers.filter(created_at__gte=today_start).count()

        grant_ledgers = CoinLedger.objects.filter(delta__gt=0)
        total_coins_recharged = int(
            paid_orders.filter(order_type=Order.TYPE_RECHARGE).aggregate(
                total=Sum("coins_granted")
            )["total"]
            or 0
        )
        today_coins_recharged = int(
            today_paid.filter(order_type=Order.TYPE_RECHARGE).aggregate(
                total=Sum("coins_granted")
            )["total"]
            or 0
        )
        if total_coins_recharged == 0:
            total_coins_recharged = int(
                grant_ledgers.filter(action_key="recharge.grant").aggregate(total=Sum("delta"))[
                    "total"
                ]
                or 0
            )

        total_wallet_balance = int(
            UserWallet.objects.aggregate(total=Sum("balance"))["total"] or 0
        )

        # 创作数：Project 模型
        from apps.creation.models import Project

        total_creations = Project.objects.count()
        today_creations = Project.objects.filter(created_at__gte=today_start).count()

        yesterday_start = today_start - timedelta(days=1)
        yesterday_paid = DashboardView._paid_orders_in_range(yesterday_start, today_start)
        yesterday_revenue = yesterday_paid.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        yesterday_creations = Project.objects.filter(
            created_at__gte=yesterday_start, created_at__lt=today_start
        ).count()
        yesterday_new_users = User.objects.filter(
            created_at__gte=yesterday_start, created_at__lt=today_start
        ).count()
        yesterday_skill_calls = spend_ledgers.filter(
            created_at__gte=yesterday_start, created_at__lt=today_start
        ).count()

        period_start = today_start - timedelta(days=29)
        period_paid = DashboardView._paid_orders_in_range(
            period_start, today_start + timedelta(days=1)
        )
        period_revenue = period_paid.aggregate(total=Sum("amount"))["total"] or Decimal("0")

        summary = {
            "total_users": total_users,
            "today_new_users": today_new_users,
            "total_members": total_members,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_creations": total_creations,
            "today_creations": today_creations,
            "today_revenue": today_revenue,
            "membership_revenue_total": membership_revenue_total,
            "recharge_revenue_total": recharge_revenue_total,
            "today_membership_yuan": today_membership_yuan,
            "today_recharge_yuan": today_recharge_yuan,
            "total_coins_spent": total_coins_spent,
            "today_coins_spent": today_coins_spent,
            "total_coins_recharged": total_coins_recharged,
            "today_coins_recharged": today_coins_recharged,
            "total_wallet_balance": total_wallet_balance,
            "today_skill_calls": today_skill_calls,
        }

        # ---- 近 30 天用户增长折线图 ----
        user_growth_30d = []
        users_cumulative = User.objects.filter(created_at__lt=today_start - timedelta(days=29)).count()
        for i in range(29, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            new_count = User.objects.filter(
                created_at__gte=day_start, created_at__lt=day_end
            ).count()
            users_cumulative += new_count
            user_growth_30d.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "new_count": new_count,
                    "total_count": users_cumulative,
                }
            )

        # ---- 会员套餐占比饼图 ----
        plans = list(MembershipPlan.objects.all())
        total_members_count = max(
            UserMembership.objects.filter(is_active=True, end_at__gt=now).count(), 1
        )
        membership_share = []
        for plan in plans:
            member_count = UserMembership.objects.filter(
                plan=plan, is_active=True, end_at__gt=now
            ).count()
            membership_share.append(
                {
                    "plan_id": plan.id,
                    "plan_name": plan.name,
                    "member_count": member_count,
                    "percentage": round(member_count / total_members_count * 100, 2),
                }
            )

        # ---- 近 7 天创作数柱状图 ----
        creation_7d = []
        finance_7d = []
        skill_calls_7d = []
        for i in range(6, -1, -1):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            count = Project.objects.filter(
                created_at__gte=day_start, created_at__lt=day_end
            ).count()
            creation_7d.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "count": count,
                }
            )
            day_paid = DashboardView._paid_orders_in_range(day_start, day_end)
            day_spend = CoinLedger.objects.filter(
                entry_type=CoinLedger.TYPE_SPEND,
                created_at__gte=day_start,
                created_at__lt=day_end,
            )
            day_grant = CoinLedger.objects.filter(
                delta__gt=0,
                created_at__gte=day_start,
                created_at__lt=day_end,
            )
            finance_7d.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "recharge_yuan": day_paid.filter(order_type=Order.TYPE_RECHARGE).aggregate(
                        total=Sum("amount")
                    )["total"]
                    or Decimal("0"),
                    "membership_yuan": day_paid.filter(order_type=Order.TYPE_MEMBERSHIP).aggregate(
                        total=Sum("amount")
                    )["total"]
                    or Decimal("0"),
                    "coins_spent": abs(
                        day_spend.aggregate(total=Sum("delta"))["total"] or 0
                    ),
                    "coins_granted": int(
                        day_grant.aggregate(total=Sum("delta"))["total"] or 0
                    ),
                    "skill_calls": day_spend.count(),
                }
            )
            skill_calls_7d.append(
                {
                    "date": day_start.strftime("%Y-%m-%d"),
                    "call_count": day_spend.count(),
                }
            )

        # ---- 近 30 天 AI 扣费 Top ----
        from apps.agent.runtime import action_key_agent_meta

        skill_since = today_start - timedelta(days=29)
        skill_rows = (
            CoinLedger.objects.filter(
                entry_type=CoinLedger.TYPE_SPEND,
                created_at__gte=skill_since,
            )
            .values("action_key")
            .annotate(
                call_count=Count("id"),
                coins_total=Sum("delta"),
            )
            .order_by("-call_count")[:12]
        )
        skill_usage_top = []
        for row in skill_rows:
            action_key = row["action_key"] or "unknown"
            item = {
                "action_key": action_key,
                "display_name": BillingService.action_display_name(action_key),
                "call_count": row["call_count"],
                "coins_total": abs(int(row["coins_total"] or 0)),
            }
            item.update(action_key_agent_meta(action_key))
            skill_usage_top.append(item)

        from apps.console.creation.project_views import (
            build_agent_ops_dashboard,
            build_creation_ops_alerts,
        )
        from apps.skill.llm.usage_log import LlmUsageService

        llm_usage = LlmUsageService.dashboard_payload(days=30)
        summary["today_llm_call_count"] = llm_usage["summary"]["today_call_count"]
        summary["today_llm_total_tokens"] = llm_usage["summary"]["today_total_tokens"]
        summary["today_llm_prompt_tokens"] = llm_usage["summary"]["today_prompt_tokens"]
        summary["today_llm_completion_tokens"] = llm_usage["summary"]["today_completion_tokens"]
        summary["today_llm_estimated_cost_yuan"] = llm_usage["summary"]["today_estimated_cost_yuan"]
        summary["today_llm_estimated_input_cost_yuan"] = llm_usage["summary"]["today_estimated_input_cost_yuan"]
        summary["today_llm_estimated_output_cost_yuan"] = llm_usage["summary"]["today_estimated_output_cost_yuan"]
        summary["period_llm_call_count"] = llm_usage["summary"]["period_call_count"]
        summary["period_llm_total_tokens"] = llm_usage["summary"]["period_total_tokens"]
        summary["period_llm_prompt_tokens"] = llm_usage["summary"]["period_prompt_tokens"]
        summary["period_llm_completion_tokens"] = llm_usage["summary"]["period_completion_tokens"]
        summary["period_llm_estimated_cost_yuan"] = llm_usage["summary"]["period_estimated_cost_yuan"]
        summary["period_llm_estimated_input_cost_yuan"] = llm_usage["summary"]["period_estimated_input_cost_yuan"]
        summary["period_llm_estimated_output_cost_yuan"] = llm_usage["summary"]["period_estimated_output_cost_yuan"]

        period_llm_cost = float(summary["period_llm_estimated_cost_yuan"] or 0)
        summary["period_revenue_yuan"] = float(period_revenue or 0)
        summary["today_gross_yuan"] = float(summary["today_revenue"] or 0) - float(
            summary["today_llm_estimated_cost_yuan"] or 0
        )
        summary["period_gross_yuan"] = float(period_revenue or 0) - period_llm_cost

        agent_ops = build_agent_ops_dashboard()
        exec_today = (agent_ops.get("execution") or {}).get("summary", {}).get("today") or {}
        exec_yesterday = {}
        runs_7d = (agent_ops.get("execution") or {}).get("runs_7d") or []
        if len(runs_7d) >= 2:
            exec_yesterday = runs_7d[-2]

        llm_7d = llm_usage.get("llm_usage_7d") or []
        yesterday_llm_cost = float(llm_7d[-2]["estimated_cost_yuan"]) if len(llm_7d) >= 2 else 0.0
        yesterday_llm_tokens = int(llm_7d[-2]["total_tokens"]) if len(llm_7d) >= 2 else 0

        compare = {
            "revenue_yuan": {
                "today": float(today_revenue),
                "yesterday": float(yesterday_revenue),
            },
            "creations": {
                "today": today_creations,
                "yesterday": yesterday_creations,
            },
            "new_users": {
                "today": today_new_users,
                "yesterday": yesterday_new_users,
            },
            "skill_calls": {
                "today": today_skill_calls,
                "yesterday": yesterday_skill_calls,
            },
            "llm_cost_yuan": {
                "today": float(summary["today_llm_estimated_cost_yuan"] or 0),
                "yesterday": yesterday_llm_cost,
            },
            "llm_tokens": {
                "today": int(summary["today_llm_total_tokens"] or 0),
                "yesterday": yesterday_llm_tokens,
            },
            "agent_runs": {
                "today": int(exec_today.get("run_count") or 0),
                "yesterday": int(exec_yesterday.get("run_count") or 0),
            },
            "agent_failed": {
                "today": int(exec_today.get("failed_count") or 0),
                "yesterday": int(exec_yesterday.get("failed_count") or 0),
            },
        }

        return {
            "summary": summary,
            "compare": compare,
            "ops_alerts": build_creation_ops_alerts(),
            "commerce_alerts": build_commerce_ops_alerts(),
            "user_growth_30d": user_growth_30d,
            "membership_share": membership_share,
            "creation_7d": creation_7d,
            "finance_7d": finance_7d,
            "skill_usage_top": skill_usage_top,
            "skill_calls_7d": skill_calls_7d,
            "agent_ops": agent_ops,
            "llm_usage": llm_usage,
        }

    def get(self, request):
        cache_key = CACHE_KEY_DASHBOARD
        data = cache.get(cache_key)
        if data:
            serializer = DashboardDataSerializer(data=data)
            if serializer.is_valid():
                return api_ok(serializer.validated_data)
            cache.delete(cache_key)

        data = self._compute_dashboard()
        cache.set(cache_key, data, CACHE_TTL)
        serializer = DashboardDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return api_ok(serializer.validated_data)
