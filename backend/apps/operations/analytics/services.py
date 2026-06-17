"""运营数据分析层。

设计目标：
  ① 五大看板：核心大盘 / 用户分析 / 创作分析 / 转化分析 / 功能使用
  ② 全部使用 ORM 聚合查询，不依赖外部数仓
  ③ 支持按日/周/月/自定义区间统计
  ④ 复用现有模型（User / Project / Order / UserCoinLedger / SkillInvoker 等）
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

User = get_user_model()


def _parse_range(params: dict) -> tuple[datetime, datetime]:
    """解析查询参数 → (start, end)。"""
    end = timezone.now()
    start = end - timedelta(days=7)
    days = int(params.get("days", 7) or 7)
    if days in (7, 14, 30, 90):
        start = end - timedelta(days=days)
    elif days > 0:
        start = end - timedelta(days=days)
    if "start" in params:
        try:
            start = datetime.fromisoformat(params["start"])
        except (TypeError, ValueError):
            pass
    if "end" in params:
        try:
            end = datetime.fromisoformat(params["end"])
        except (TypeError, ValueError):
            pass
    return start, end


# ──────────────────────────────────────────────
# 1. 核心大盘
# ──────────────────────────────────────────────
def core_overview(params: dict) -> dict:
    start, end = _parse_range(params)
    prev_start = start - (end - start)
    prev_end = start

    new_users = User.objects.filter(date_joined__gte=start, date_joined__lt=end).count()
    new_users_prev = User.objects.filter(
        date_joined__gte=prev_start, date_joined__lt=prev_end,
    ).count()
    active_users = _active_users(start, end)
    active_users_prev = _active_users(prev_start, prev_end)
    total_users = User.objects.count()

    return {
        "range": {"start": start, "end": end},
        "metrics": {
            "new_users": _with_delta(new_users, new_users_prev),
            "active_users": _with_delta(active_users, active_users_prev),
            "total_users": total_users,
        },
    }


def _active_users(start: datetime, end: datetime) -> int:
    """活跃用户：以 Project 创作为准（最近 7 天有 project 创建）。"""
    try:
        from apps.creation.models import Project
        return Project.objects.filter(
            created_at__gte=start, created_at__lt=end,
        ).values("user_id").distinct().count()
    except Exception:  # noqa: BLE001
        return 0


def _with_delta(curr: int, prev: int) -> dict:
    if prev <= 0:
        delta_pct = None if curr <= 0 else 1.0
    else:
        delta_pct = round((curr - prev) / prev, 4)
    return {"value": curr, "prev": prev, "delta_pct": delta_pct}


# ──────────────────────────────────────────────
# 2. 用户分析
# ──────────────────────────────────────────────
def user_analytics(params: dict) -> dict:
    start, end = _parse_range(params)
    cohort_days = int(params.get("cohort_days", 7))

    # 留存：以注册日为 cohort，统计第 N 日活跃
    retention_rows = []
    for offset in (0, 1, 3, 7, 14, 30):
        if offset > 90:
            continue
        cohort_start = start - timedelta(days=offset)
        cohort_end = cohort_start + timedelta(days=1)
        size = User.objects.filter(
            date_joined__gte=cohort_start, date_joined__lt=cohort_end,
        ).count()
        if size <= 0:
            continue
        try:
            from apps.creation.models import Project
            retained = Project.objects.filter(
                user__date_joined__gte=cohort_start, user__date_joined__lt=cohort_end,
                created_at__gte=cohort_start + timedelta(days=1),
                created_at__lt=cohort_start + timedelta(days=offset + 2),
            ).values("user_id").distinct().count()
        except Exception:  # noqa: BLE001
            retained = 0
        retention_rows.append({
            "offset_days": offset,
            "cohort_size": size,
            "retained": retained,
            "rate": round(retained / size, 4) if size else 0,
        })

    # 用户分层：按总创作数分桶
    segments = _user_segments(start, end)

    return {
        "range": {"start": start, "end": end},
        "retention": retention_rows,
        "segments": segments,
    }


def _user_segments(start: datetime, end: datetime) -> list:
    try:
        from apps.creation.models import Project
    except Exception:  # noqa: BLE001
        return []
    rows = (
        Project.objects.values("user_id")
        .annotate(c=Count("id"))
        .values("user_id", "c")
    )
    buckets = {
        "new": 0,         # 0 项目
        "casual": 0,      # 1-2
        "active": 0,      # 3-9
        "core": 0,        # 10-29
        "ambassador": 0,  # 30+
    }
    project_count = {row["user_id"]: row["c"] for row in rows}
    all_users = set(User.objects.values_list("id", flat=True))
    for uid in all_users:
        c = project_count.get(uid, 0)
        if c == 0:
            buckets["new"] += 1
        elif c <= 2:
            buckets["casual"] += 1
        elif c <= 9:
            buckets["active"] += 1
        elif c <= 29:
            buckets["core"] += 1
        else:
            buckets["ambassador"] += 1
    return [{"segment": k, "count": v} for k, v in buckets.items()]


# ──────────────────────────────────────────────
# 3. 创作分析
# ──────────────────────────────────────────────
def creation_analytics(params: dict) -> dict:
    start, end = _parse_range(params)
    try:
        from apps.creation.models import Project
    except Exception:  # noqa: BLE001
        return {"error": "creation app 未安装"}

    base = Project.objects.filter(created_at__gte=start, created_at__lt=end)
    total = base.count()
    completed = base.filter(status="completed").count()
    failed = base.filter(status="failed").count()
    completion_rate = round(completed / total, 4) if total else 0

    by_pipeline_mode = list(base.values("pipeline_mode").annotate(count=Count("id")))

    # 趋势
    trend = _daily_trend(base, "created_at", days=(end - start).days)

    # 平均质量分
    avg_score = base.filter(overall_score__isnull=False).aggregate(s=Avg("overall_score"))["s"]
    grade_distribution = list(
        base.exclude(grade__isnull=True).exclude(grade="").values("grade").annotate(count=Count("id")),
    )

    return {
        "range": {"start": start, "end": end},
        "metrics": {
            "total_projects": total,
            "completed": completed,
            "failed": failed,
            "completion_rate": completion_rate,
            "avg_score": round(avg_score, 2) if avg_score else None,
        },
        "by_pipeline_mode": by_pipeline_mode,
        "grade_distribution": grade_distribution,
        "trend": trend,
    }


# ──────────────────────────────────────────────
# 4. 转化分析
# ──────────────────────────────────────────────
def conversion_analytics(params: dict) -> dict:
    start, end = _parse_range(params)
    try:
        from apps.orders.models import Order
    except Exception:  # noqa: BLE001
        return {"error": "orders app 未安装"}

    orders = Order.objects.filter(created_at__gte=start, created_at__lt=end)
    paid = orders.filter(status="paid")
    revenue = paid.aggregate(s=Sum("amount"))["s"] or 0
    paying_users = paid.values("user_id").distinct().count()
    new_users = User.objects.filter(date_joined__gte=start, date_joined__lt=end).count()
    total_users = User.objects.count()
    arpu = round(revenue / total_users, 2) if total_users else 0
    pay_rate = round(paying_users / new_users, 4) if new_users else 0

    # 漏斗
    funnel = _funnel(start, end)

    return {
        "range": {"start": start, "end": end},
        "metrics": {
            "revenue": float(revenue),
            "paying_users": paying_users,
            "new_users": new_users,
            "pay_rate": pay_rate,
            "arpu": arpu,
        },
        "funnel": funnel,
    }


def _funnel(start: datetime, end: datetime) -> list:
    steps = []
    new_users = User.objects.filter(date_joined__gte=start, date_joined__lt=end).count()
    steps.append({"step": "register", "count": new_users})
    try:
        from apps.creation.models import Project
        submitted = Project.objects.filter(
            created_at__gte=start, created_at__lt=end,
        ).values("user_id").distinct().count()
        steps.append({"step": "submit_creation", "count": submitted})
        completed = Project.objects.filter(
            created_at__gte=start, created_at__lt=end, status="completed",
        ).values("user_id").distinct().count()
        steps.append({"step": "complete_creation", "count": completed})
    except Exception:  # noqa: BLE001
        pass
    try:
        from apps.orders.models import Order
        paid = Order.objects.filter(
            created_at__gte=start, created_at__lt=end, status="paid",
        ).values("user_id").distinct().count()
        steps.append({"step": "first_pay", "count": paid})
    except Exception:  # noqa: BLE001
        pass
    return steps


# ──────────────────────────────────────────────
# 5. 功能使用分析
# ──────────────────────────────────────────────
def feature_usage_analytics(params: dict) -> dict:
    start, end = _parse_range(params)

    rows = {"skills": [], "templates": [], "agents": []}

    # 技能调用 Top
    try:
        from apps.skill.models import AgentSkillDefinition
        from apps.creation.monitoring.agent_execution_log import AgentExecutionLog  # type: ignore
        skill_usage = (
            AgentExecutionLog.objects
            .filter(created_at__gte=start, created_at__lt=end)
            .values("agent_id")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        rows["skills"] = list(skill_usage)
    except Exception:  # noqa: BLE001
        pass

    # 模板使用 Top
    try:
        from apps.creation.models import Project
        from apps.workflow.models import FusionPipelinePack
        pack_usage = (
            Project.objects.filter(created_at__gte=start, created_at__lt=end)
            .values("pipeline_pack_id")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        ids = [r["pipeline_pack_id"] for r in pack_usage if r["pipeline_pack_id"]]
        names = dict(FusionPipelinePack.objects.filter(id__in=ids).values_list("id", "display_name"))
        rows["templates"] = [
            {"pack_id": r["pipeline_pack_id"], "name": names.get(r["pipeline_pack_id"], "—"), "count": r["count"]}
            for r in pack_usage
        ]
    except Exception:  # noqa: BLE001
        pass

    return {"range": {"start": start, "end": end}, "data": rows}


# ──────────────────────────────────────────────
# 6. 趋势工具
# ──────────────────────────────────────────────
def _daily_trend(qs, field_name: str, *, days: int) -> list:
    if days <= 0:
        days = 1
    if days > 90:
        days = 90
    rows = []
    today = timezone.now().date()
    for i in range(days, -1, -1):
        d = today - timedelta(days=i)
        next_d = d + timedelta(days=1)
        c = qs.filter(**{
            f"{field_name}__date__gte": d,
            f"{field_name}__date__lt": next_d,
        }).count()
        rows.append({"date": d.isoformat(), "count": c})
    return rows
