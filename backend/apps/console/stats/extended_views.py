# -*- coding: utf-8 -*-
"""
数据统计中心扩展 API

补充 stats/summary/ 之外的精细化数据：
- 调用量趋势
- 技能使用排行
- 失败率 Top N
- LLM Provider 用量
- 创作节点耗时分布
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict, List

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdminUser
from apps.common.pagination import StandardPagination
from apps.console.responses import api_fail, api_ok

logger = logging.getLogger(__name__)


# ============================================================
# 内部辅助：分桶与百分位
# ============================================================

def _parse_days_param(request, default: int = 7, choices=(7, 30, 90)) -> int:
    """解析 days 入参，限定合法区间。"""
    try:
        days = int(request.query_params.get("days", default))
    except (TypeError, ValueError):
        days = default
    if days <= 0:
        days = default
    if choices and days not in choices:
        # 离合法值最近的允许值
        days = min(choices, key=lambda c: abs(c - days))
    return days


def _percentile(sorted_values: List[int], pct: float) -> int:
    """线性插值近似百分位（毫秒级精度足够）。"""
    if not sorted_values:
        return 0
    if pct <= 0:
        return int(sorted_values[0])
    if pct >= 100:
        return int(sorted_values[-1])
    rank = (pct / 100.0) * (len(sorted_values) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = rank - lo
    return int(round(sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac))


# ============================================================
# 1) 调用量趋势
# ============================================================

class StatsTrendView(APIView):
    """GET /api/admin/stats/trend/

    入参：days (7/30/90)
    返回：{
      "data": [
        {"date": "2026-06-10", "calls": 1234, "success_rate": 95.5},
        ...
      ]
    }
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = _parse_days_param(request, default=7)
        except Exception:  # noqa: BLE001
            days = 7

        try:
            from apps.skill.models import LlmUsageLog
            from apps.skill.llm.usage_log import LlmUsageService

            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            since = today_start - timedelta(days=days - 1)

            base_qs = (
                LlmUsageLog.objects.filter(created_at__gte=since)
                .exclude(LlmUsageService.junk_log_filter())
            )

            # 聚合：每日成功 / 失败 / 总数
            rows = (
                base_qs.annotate(day=TruncDate("created_at"))
                .values("day")
                .annotate(
                    calls=Count("id"),
                    success_calls=Count("id", filter=Q(success=True)),
                )
                .order_by("day")
            )
            daily_map: Dict[str, Dict[str, int]] = {
                str(row["day"]): {
                    "calls": int(row["calls"] or 0),
                    "success_calls": int(row["success_calls"] or 0),
                }
                for row in rows
                if row.get("day") is not None
            }

            data: List[Dict[str, Any]] = []
            for i in range(days - 1, -1, -1):
                day_start = today_start - timedelta(days=i)
                day_str = day_start.strftime("%Y-%m-%d")
                row = daily_map.get(day_str, {"calls": 0, "success_calls": 0})
                total = row["calls"]
                success = row["success_calls"]
                success_rate = round((success / total) * 100, 2) if total > 0 else 0.0
                data.append(
                    {
                        "date": day_str,
                        "calls": total,
                        "success_calls": success,
                        "success_rate": success_rate,
                    }
                )

            return api_ok(
                {
                    "data": data,
                    "days": days,
                    "total_calls": sum(item["calls"] for item in data),
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("StatsTrendView 失败: %s", exc)
            return api_ok({"data": [], "days": days, "total_calls": 0})


# ============================================================
# 2) 技能使用排行
# ============================================================

class SkillRankingView(APIView):
    """GET /api/admin/stats/skill-ranking/

    入参：days (7/30/90), limit (默认 20)
    返回：{
      "items": [
        {"skill_id": "brief.project_definition", "calls": 234, "success_rate": 97.3},
        ...
      ]
    }
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = _parse_days_param(request, default=30)
            try:
                limit = int(request.query_params.get("limit", 20))
            except (TypeError, ValueError):
                limit = 20
            limit = max(1, min(limit, 100))

            from apps.skill.models import LlmUsageLog
            from apps.skill.llm.usage_log import LlmUsageService

            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            since = today_start - timedelta(days=days - 1)

            base_qs = (
                LlmUsageLog.objects.filter(created_at__gte=since)
                .exclude(source_key="")
                .exclude(LlmUsageService.junk_log_filter())
            )

            rows = (
                base_qs.values("source_type", "source_key")
                .annotate(
                    calls=Count("id"),
                    success_calls=Count("id", filter=Q(success=True)),
                )
                .order_by("-calls")[:limit]
            )

            items: List[Dict[str, Any]] = []
            for row in rows:
                calls = int(row["calls"] or 0)
                success_calls = int(row["success_calls"] or 0)
                success_rate = round((success_calls / calls) * 100, 2) if calls > 0 else 0.0
                items.append(
                    {
                        "source_type": row["source_type"],
                        "skill_id": row["source_key"],
                        "calls": calls,
                        "success_calls": success_calls,
                        "success_rate": success_rate,
                    }
                )

            return api_ok({"items": items, "days": days})
        except Exception as exc:  # noqa: BLE001
            logger.warning("SkillRankingView 失败: %s", exc)
            return api_ok({"items": [], "days": days if "days" in locals() else 30})


# ============================================================
# 3) 失败率 Top N
# ============================================================

class FailureRankingView(APIView):
    """GET /api/admin/stats/failure-ranking/

    失败率 = 失败次数 / 总调用次数；只统计 calls >= 5 的技能，避免低样本偏差。
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = _parse_days_param(request, default=30)
            try:
                limit = int(request.query_params.get("limit", 10))
            except (TypeError, ValueError):
                limit = 10
            limit = max(1, min(limit, 50))
            min_calls = 5

            from apps.skill.models import LlmUsageLog
            from apps.skill.llm.usage_log import LlmUsageService

            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            since = today_start - timedelta(days=days - 1)

            base_qs = (
                LlmUsageLog.objects.filter(created_at__gte=since)
                .exclude(source_key="")
                .exclude(LlmUsageService.junk_log_filter())
            )

            rows = (
                base_qs.values("source_type", "source_key")
                .annotate(
                    calls=Count("id"),
                    failed_calls=Count("id", filter=Q(success=False)),
                )
                .order_by("-failed_calls")
            )

            items: List[Dict[str, Any]] = []
            for row in rows:
                calls = int(row["calls"] or 0)
                failed = int(row["failed_calls"] or 0)
                if calls < min_calls or failed <= 0:
                    continue
                failure_rate = round((failed / calls) * 100, 2)
                items.append(
                    {
                        "source_type": row["source_type"],
                        "skill_id": row["source_key"],
                        "calls": calls,
                        "failed_calls": failed,
                        "failure_rate": failure_rate,
                    }
                )

            # 按失败率降序
            items.sort(key=lambda r: r["failure_rate"], reverse=True)
            items = items[:limit]

            return api_ok({"items": items, "days": days})
        except Exception as exc:  # noqa: BLE001
            logger.warning("FailureRankingView 失败: %s", exc)
            return api_ok({"items": [], "days": days if "days" in locals() else 30})


# ============================================================
# 4) LLM Provider 用量分布
# ============================================================

class LlmProviderUsageView(APIView):
    """GET /api/admin/stats/llm-provider-usage/

    按 model_name + provider_name 聚合，返回调用次数 / 估算费用 / 占比。
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = _parse_days_param(request, default=30)

            from apps.skill.models import LlmUsageLog
            from apps.skill.llm.usage_log import LlmUsageService

            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            since = today_start - timedelta(days=days - 1)

            base_qs = (
                LlmUsageLog.objects.filter(created_at__gte=since, success=True)
                .exclude(LlmUsageService.junk_log_filter())
            )

            rows = (
                base_qs.values("provider_name", "model_name")
                .annotate(
                    calls=Count("id"),
                    cost=Sum("estimated_cost_yuan"),
                    total_tokens=Sum("total_tokens"),
                )
                .order_by("-calls")
            )

            # 计算 total_calls 用于占比
            total_calls = sum(int(r["calls"] or 0) for r in rows) or 1

            items: List[Dict[str, Any]] = []
            for row in rows:
                calls = int(row["calls"] or 0)
                cost = float(row["cost"] or 0)
                items.append(
                    {
                        "provider": row["provider_name"] or "未命名",
                        "model": row["model_name"] or "unknown",
                        "calls": calls,
                        "cost_yuan": round(cost, 4),
                        "total_tokens": int(row["total_tokens"] or 0),
                        "ratio": round((calls / total_calls) * 100, 2),
                    }
                )

            return api_ok(
                {
                    "items": items,
                    "days": days,
                    "total_calls": total_calls,
                    "total_cost_yuan": round(sum(i["cost_yuan"] for i in items), 4),
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("LlmProviderUsageView 失败: %s", exc)
            return api_ok({"items": [], "days": days if "days" in locals() else 30})


# ============================================================
# 5) 创作节点耗时分布
# ============================================================

class NodeDurationDistributionView(APIView):
    """GET /api/admin/stats/node-duration/

    按 AgentExecutionRun.agent_id 聚合 finished_at - started_at 的耗时分布。
    仅统计 status=completed 的记录。
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = _parse_days_param(request, default=30)

            from apps.creation.models import AgentExecutionRun

            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            since = today_start - timedelta(days=days - 1)

            # 限制样本数，避免百万行迭代
            sample_limit = 5000
            qs = (
                AgentExecutionRun.objects.filter(
                    started_at__gte=since,
                    status=AgentExecutionRun.STATUS_COMPLETED,
                    started_at__isnull=False,
                    finished_at__isnull=False,
                )
                .order_by("-started_at")
            )

            # 先 aggregate 总数
            total = qs.count()
            if total > sample_limit:
                # 用子查询取最近 N 条
                ids = list(qs.values_list("id", flat=True)[:sample_limit])
                qs = AgentExecutionRun.objects.filter(id__in=ids)

            buckets: Dict[str, List[int]] = {}
            for run in qs.iterator(chunk_size=500):
                try:
                    delta_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
                except Exception:  # noqa: BLE001
                    continue
                if delta_ms < 0:
                    continue
                buckets.setdefault(run.agent_id, []).append(delta_ms)

            items: List[Dict[str, Any]] = []
            for agent_id, durations in buckets.items():
                durations.sort()
                total_count = len(durations)
                if total_count == 0:
                    continue
                avg_ms = int(sum(durations) / total_count)
                p50 = _percentile(durations, 50)
                p95 = _percentile(durations, 95)
                p99 = _percentile(durations, 99)
                items.append(
                    {
                        "agent_id": agent_id,
                        "run_count": total_count,
                        "avg_ms": avg_ms,
                        "p50": p50,
                        "p95": p95,
                        "p99": p99,
                    }
                )

            items.sort(key=lambda r: r["avg_ms"], reverse=True)

            return api_ok(
                {
                    "items": items,
                    "days": days,
                    "sampled": total <= sample_limit,
                    "sample_limit": sample_limit,
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("NodeDurationDistributionView 失败: %s", exc)
            return api_ok({"items": [], "days": days if "days" in locals() else 30})


# ============================================================
# 6) 顶部 KPI 汇总（数据统计中心专用）
# ============================================================

class StatsKpiView(APIView):
    """GET /api/admin/stats/kpi/ — 数据统计中心首页 KPI 卡片。

    聚合四个核心指标：
    - 今日项目数 (Project)
    - LLM 整体成功率
    - 平均耗时 (AgentExecutionRun)
    - 今日总扣币 (CoinLedger)
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            from apps.billing.models import CoinLedger
            from apps.creation.models import AgentExecutionRun, Project
            from apps.skill.models import LlmUsageLog
            from apps.skill.llm.usage_log import LlmUsageService

            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            today_projects = Project.objects.filter(created_at__gte=today_start).count()

            # LLM 整体成功率（近 7 天）
            since_7d = today_start - timedelta(days=6)
            llm_qs = LlmUsageLog.objects.filter(created_at__gte=since_7d).exclude(
                LlmUsageService.junk_log_filter()
            )
            llm_agg = llm_qs.aggregate(
                total=Count("id"),
                success=Count("id", filter=Q(success=True)),
            )
            llm_total = int(llm_agg["total"] or 0)
            llm_success = int(llm_agg["success"] or 0)
            success_rate = round((llm_success / llm_total) * 100, 2) if llm_total > 0 else 0.0

            # 平均耗时（近 7 天 completed run）
            run_qs = AgentExecutionRun.objects.filter(
                started_at__gte=since_7d,
                status=AgentExecutionRun.STATUS_COMPLETED,
                started_at__isnull=False,
                finished_at__isnull=False,
            )
            durations_ms: List[int] = []
            for run in run_qs.iterator(chunk_size=500):
                try:
                    durations_ms.append(
                        int((run.finished_at - run.started_at).total_seconds() * 1000)
                    )
                except Exception:  # noqa: BLE001
                    continue
            avg_ms = int(sum(durations_ms) / len(durations_ms)) if durations_ms else 0

            # 今日总扣币
            today_coins = int(
                abs(
                    CoinLedger.objects.filter(
                        entry_type=CoinLedger.TYPE_SPEND,
                        created_at__gte=today_start,
                    ).aggregate(total=Sum("delta"))["total"]
                    or 0
                )
            )

            return api_ok(
                {
                    "today_projects": today_projects,
                    "success_rate": success_rate,
                    "avg_duration_ms": avg_ms,
                    "today_coins_spent": today_coins,
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("StatsKpiView 失败: %s", exc)
            return api_ok(
                {
                    "today_projects": 0,
                    "success_rate": 0.0,
                    "avg_duration_ms": 0,
                    "today_coins_spent": 0,
                }
            )
