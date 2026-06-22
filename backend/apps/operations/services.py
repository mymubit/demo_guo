# -*- coding: utf-8 -*-
"""【运营 M5】运营 Dashboard 聚合服务。

5 个核心 SLO 卡片 + 内容质量/反馈/配置命中三个分析页。

设计原则：
  • 所有聚合都走 ORM（不写 SQL），便于切换数据库。
  • 高频路径加 `_cached_get`，避免冷启动时全表扫描。
  • 数字字段统一 round(x, 2)，前端可放心使用。
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.core.cache import cache
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

# 缓存 60s（运营 Dashboard 不需要实时精度）
CACHE_TTL = 60
CACHE_KEY_PREFIX = "ops:dashboard:"


# ============================================================
# 核心 SLO 卡片（5 个）
# ============================================================
def dashboard_slo_cards() -> dict:
    """运营 Dashboard 主页面：5 个核心 SLO 卡片。"""
    from apps.creation.models import Project
    from apps.billing.models import CoinLedger
    from apps.creation.models import AgentExecutionRun
    from apps.monitoring.models import ApiPerformanceLog, AlertEvent, MonitoringException

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_1h = now - timedelta(hours=1)
    last_5min = now - timedelta(minutes=5)

    cache_key = f"{CACHE_KEY_PREFIX}slo:{int(now.timestamp() // CACHE_TTL)}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # 1. 创作提交 5xx 突增（5min 窗口）
    submit_5xx_5min = MonitoringException.objects.filter(
        source=MonitoringException.Source.BUSINESS,
        created_at__gte=last_5min,
        path__icontains="/api/creation/submit",
        status_code__gte=500,
    ).count()

    # 2. 僵尸 Agent 运行（>15min 仍 running）
    threshold_15min = now - timedelta(minutes=15)
    zombie_count = AgentExecutionRun.objects.filter(
        status=AgentExecutionRun.STATUS_RUNNING,
        started_at__lt=threshold_15min,
        finished_at__isnull=True,
    ).count()

    # 3. LLM 整体失败率（5min）
    llm_qs = ApiPerformanceLog.objects.filter(
        created_at__gte=last_5min,
        path__icontains="/api/skill/llm",
    )
    llm_total = llm_qs.count()
    llm_failed = llm_qs.filter(extra__business_error=True).count()
    llm_error_rate = round(llm_failed / llm_total * 100, 2) if llm_total else 0.0

    # 4. 创作币日扣费异常（与昨日同时段 ±50%）
    cur_window_start = now - timedelta(hours=1)
    cur_total = CoinLedger.objects.filter(
        created_at__gte=cur_window_start,
        entry_type=CoinLedger.TYPE_SPEND,
    ).aggregate(total=Sum("delta"))["total"] or 0
    yesterday_start = cur_window_start - timedelta(days=1)
    yesterday_end = cur_window_start
    yesterday_total = CoinLedger.objects.filter(
        created_at__gte=yesterday_start,
        created_at__lt=yesterday_end,
        entry_type=CoinLedger.TYPE_SPEND,
    ).aggregate(total=Sum("delta"))["total"] or 0
    if yesterday_total == 0:
        coin_spend_delta_pct = 0.0
    else:
        coin_spend_delta_pct = round(
            abs(float(cur_total) - float(yesterday_total)) / abs(float(yesterday_total)) * 100, 2
        )

    # 5. Dashboard 缓存失效率（5min：avg duration > 800ms）
    dash_qs = ApiPerformanceLog.objects.filter(
        created_at__gte=last_5min,
        path__icontains="/api/admin/dashboard",
    )
    dash_avg_ms = dash_qs.aggregate(value=Avg("duration_ms"))["value"] or 0

    # 开放告警数（待处理）
    open_alerts = AlertEvent.objects.filter(status=AlertEvent.Status.OPEN).count()

    from apps.drama.progress_service import DramaProjectProgressService

    running_projects = len(set(DramaProjectProgressService.in_progress_project_ids()))
    failed_projects = len(set(DramaProjectProgressService.blocked_project_ids()))

    data = {
        "as_of": now.isoformat(),
        "slo_cards": [
            {
                "key": "submit_5xx",
                "label": "创作提交 5xx",
                "value": submit_5xx_5min,
                "window": "5min",
                "level": "P0",
                "ok": submit_5xx_5min < 5,
            },
            {
                "key": "zombie_workflow",
                "label": "僵尸 Agent 运行",
                "value": zombie_count,
                "window": "实时",
                "level": "P0",
                "ok": zombie_count == 0,
            },
            {
                "key": "llm_error_rate",
                "label": "LLM 失败率",
                "value": llm_error_rate,
                "unit": "%",
                "window": "5min",
                "level": "P0",
                "ok": llm_error_rate < 15,
            },
            {
                "key": "coin_spend_anomaly",
                "label": "创作币扣费异常",
                "value": coin_spend_delta_pct,
                "unit": "%",
                "window": "1h vs 昨日同时段",
                "level": "P1",
                "ok": coin_spend_delta_pct < 50,
            },
            {
                "key": "dashboard_cache",
                "label": "Dashboard 平均耗时",
                "value": round(float(dash_avg_ms), 0),
                "unit": "ms",
                "window": "5min",
                "level": "P2",
                "ok": float(dash_avg_ms) < 800,
            },
        ],
        "open_alerts": open_alerts,
        # 简版 dashboard 摘要（供首页快速预览）
        "snapshot": {
            "today_projects": Project.objects.filter(created_at__gte=today_start).count(),
            "running_projects": running_projects,
            "failed_projects": failed_projects,
        },
    }
    cache.set(cache_key, data, CACHE_TTL)
    return data


# ============================================================
# 内容质量聚合（M2 配合）
# ============================================================
def content_quality_dashboard(days: int = 30) -> dict:
    """运营 M2 看板：保存率/导出率/弃用率 + 卡点人群。"""
    from apps.creation.services.content_quality import (
        content_quality_funnel,
        content_quality_summary,
        stuck_projects,
    )

    cache_key = f"{CACHE_KEY_PREFIX}content_quality:{days}:{int(timezone.now().timestamp() // CACHE_TTL)}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    data = {
        "summary": content_quality_summary(days=days),
        "funnel": content_quality_funnel(days=days),
        "stuck_projects": stuck_projects(days=3, limit=30),
    }
    cache.set(cache_key, data, CACHE_TTL)
    return data


# ============================================================
# 反馈汇总
# ============================================================
def feedback_summary(days: int = 30) -> dict:
    from .models import CreationFeedback

    cache_key = f"{CACHE_KEY_PREFIX}feedback:{days}:{int(timezone.now().timestamp() // CACHE_TTL)}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    now = timezone.now()
    threshold_dt = now - timedelta(days=days)
    qs = CreationFeedback.objects.filter(created_at__gte=threshold_dt)

    by_category = list(
        qs.values("category").annotate(count=Count("id")).order_by("-count")
    )
    by_severity = list(
        qs.values("severity").annotate(count=Count("id")).order_by("-count")
    )
    by_status = list(qs.values("status").annotate(count=Count("id")))

    open_count = qs.filter(status="open").count()
    in_progress_count = qs.filter(status="in_progress").count()
    resolved_count = qs.filter(status="resolved").count()
    p0_open = qs.filter(severity="P0", status__in=["open", "in_progress"]).count()

    data = {
        "window_days": days,
        "total": qs.count(),
        "open": open_count,
        "in_progress": in_progress_count,
        "resolved": resolved_count,
        "p0_open": p0_open,
        "by_category": by_category,
        "by_severity": by_severity,
        "by_status": by_status,
    }
    cache.set(cache_key, data, CACHE_TTL)
    return data


# ============================================================
# 配置命中率分析
# ============================================================
def config_hit_dashboard(limit: int = 30) -> dict:
    from apps.system_config.models import SystemConfigItem

    cache_key = f"{CACHE_KEY_PREFIX}config_hit:{limit}:{int(timezone.now().timestamp() // CACHE_TTL)}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    qs = SystemConfigItem.objects.filter(
        deleted_at__isnull=True, is_active=True
    ).exclude(hit_count=0).order_by("-hit_count")[:limit]

    items = []
    for c in qs:
        items.append({
            "config_key": c.config_key,
            "config_name": c.config_name,
            "category_code": c.category.code,
            "category_name": c.category.name,
            "is_sensitive": c.is_sensitive,
            "is_public": c.is_public,
            "hit_count": c.hit_count,
            "hit_24h": c.hit_24h,
            "last_hit_at": c.last_hit_at.isoformat() if c.last_hit_at else "",
            "version": c.version,
        })

    # 24h 热点
    hot_24h = list(
        SystemConfigItem.objects.filter(
            deleted_at__isnull=True, is_active=True, hit_24h__gt=0,
        ).order_by("-hit_24h").values(
            "config_key", "config_name", "hit_24h", "hit_count"
        )[:limit]
    )

    # 死代码候选：总命中 < 10 且创建 > 7 天
    threshold_dt = timezone.now() - timedelta(days=7)
    dead = list(
        SystemConfigItem.objects.filter(
            deleted_at__isnull=True,
            is_active=True,
            hit_count__lt=10,
            created_at__lt=threshold_dt,
        ).order_by("hit_count").values(
            "config_key", "config_name", "hit_count", "last_hit_at",
        )[:limit]
    )

    data = {
        "top_total": items,
        "top_24h": hot_24h,
        "dead_candidates": dead,
        "total_active": SystemConfigItem.objects.filter(
            deleted_at__isnull=True, is_active=True
        ).count(),
        "touched_24h": SystemConfigItem.objects.filter(
            deleted_at__isnull=True, is_active=True, hit_24h__gt=0
        ).count(),
    }
    cache.set(cache_key, data, CACHE_TTL)
    return data


# ============================================================
# 节点耗时分析（来自 monitoring + workflow）
# ============================================================
def node_duration_dashboard(days: int = 7) -> dict:
    """Agent 执行耗时分布（来自 AgentExecutionRun）。"""
    from django.db.models import DurationField, ExpressionWrapper, F, FloatField
    from django.db.models.functions import Extract

    from apps.creation.models import AgentExecutionRun

    cache_key = f"{CACHE_KEY_PREFIX}node_dur:{days}:{int(timezone.now().timestamp() // CACHE_TTL)}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    now = timezone.now()
    threshold_dt = now - timedelta(days=days)

    base_qs = AgentExecutionRun.objects.filter(
        started_at__gte=threshold_dt,
        finished_at__isnull=False,
    ).annotate(
        duration=ExpressionWrapper(
            F("finished_at") - F("started_at"),
            output_field=DurationField(),
        ),
        duration_seconds=Extract("duration", "epoch", output_field=FloatField()),
    )

    by_node = list(
        base_qs.filter(node_index__isnull=False)
        .values("node_index", "agent_id")
        .annotate(
            avg_seconds=Avg("duration_seconds"),
            sample_count=Count("id"),
        )
        .order_by("node_index")
    )

    by_agent = list(
        base_qs.values("agent_id")
        .annotate(
            avg_seconds=Avg("duration_seconds"),
            sample_count=Count("id"),
        )
        .order_by("-sample_count")[:20]
    )

    failed_by_node = list(
        AgentExecutionRun.objects.filter(
            started_at__gte=threshold_dt,
            status=AgentExecutionRun.STATUS_FAILED,
            node_index__isnull=False,
        )
        .values("node_index", "agent_id")
        .annotate(failed_count=Count("id"))
        .order_by("-failed_count")[:10]
    )

    data = {
        "window_days": days,
        "by_node": by_node,
        "by_agent": by_agent,
        "failed_by_node": failed_by_node,
    }
    cache.set(cache_key, data, CACHE_TTL)
    return data


# ============================================================
# 综合 dashboard 摘要（主页面用）
# ============================================================
def full_dashboard(days: int = 30) -> dict:
    """运营 Dashboard 主页面：聚合所有看板数据。"""
    cache_key = f"{CACHE_KEY_PREFIX}full:{days}:{int(timezone.now().timestamp() // CACHE_TTL)}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    data = {
        "slo": dashboard_slo_cards(),
        "content_quality": content_quality_dashboard(days=days),
        "feedback": feedback_summary(days=days),
        "config_hit": config_hit_dashboard(),
        "node_duration": node_duration_dashboard(days=7),
    }
    cache.set(cache_key, data, CACHE_TTL)
    return data


# ============================================================
# 抽样回访辅助
# ============================================================
def sample_projects_for_feedback(*, days: int = 7, limit: int = 20) -> list[dict]:
    """抽样候选：abandoned/completed/低分项目，运营可一键回访并录入反馈。

    返回结构：每条包含 project_id / title / status / final_export_count / user_id / user_phone。
    """
    from apps.creation.models import Project

    now = timezone.now()
    threshold_dt = now - timedelta(days=days)

    from apps.drama.progress_service import DramaProjectProgressService

    deliverable_ids = set(DramaProjectProgressService.deliverable_project_ids())
    blocked_ids = set(DramaProjectProgressService.blocked_project_ids())

    qs = Project.objects.filter(
        created_at__gte=threshold_dt,
        is_quality_sampled=False,
    ).filter(
        Q(abandoned_at__isnull=False)
        | Q(id__in=blocked_ids)
        | (Q(final_export_count=0) & Q(id__in=deliverable_ids))
    ).select_related("user").order_by("-created_at")[:limit]

    return [
        {
            "project_id": str(p.id),
            "title": (p.title or p.theme or "未命名")[:200],
            "theme": p.theme,
            "status": p.execution_status,
            "status_text": dict(Project.STATUS_CHOICES).get(p.execution_status, p.execution_status),
            "user_edit_count": p.user_edit_count,
            "final_export_count": p.final_export_count,
            "abandoned_at": p.abandoned_at.isoformat() if p.abandoned_at else "",
            "overall_score": p.overall_score,
            "grade": p.grade or "",
            "user_id": str(p.user_id) if p.user_id else "",
            "user_phone": getattr(p.user, "phone", "") or "",
            "created_at": p.created_at.isoformat() if p.created_at else "",
        }
        for p in qs
    ]


def mark_projects_sampled(project_ids: list[str]) -> int:
    """标记项目为「已采样」，避免重复回访。"""
    from apps.creation.models import Project

    if not project_ids:
        return 0
    return Project.objects.filter(id__in=project_ids).update(is_quality_sampled=True)


# ============================================================
# 用户行为埋点（M6）
# ============================================================
def track_event(
    *,
    event_name: str,
    user=None,
    session_id: str = "",
    project_id: str = "",
    page: str = "",
    payload: dict | None = None,
    source: str = "backend",
    request=None,
) -> bool:
    """统一埋点入口（供后端业务路径调用）。

    fire-and-forget：失败仅记日志，不抛异常（埋点不能影响主流程）。
    """
    from .models import UserBehaviorEvent

    valid_events = {choice.value for choice in UserBehaviorEvent.EventName}
    if event_name not in valid_events:
        logger.warning("[Tracking] 非法 event_name=%s", event_name)
        return False

    try:
        ip = ""
        ua = ""
        if request is not None:
            ip = request.META.get("REMOTE_ADDR", "") or ""
            ua = (request.META.get("HTTP_USER_AGENT", "") or "")[:512]
        UserBehaviorEvent.objects.create(
            event_name=event_name,
            source=source,
            user=user if getattr(user, "is_authenticated", False) else None,
            session_id=(session_id or "")[:64],
            project_id=(project_id or "")[:64],
            page=(page or "")[:200],
            ip_address=ip or None,
            user_agent=ua,
            payload=payload or {},
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("[Tracking] 写入事件失败: %s", exc)
        return False


def behavior_funnel(days: int = 7) -> dict:
    """用户行为漏斗：6 个事件在过去 N 天的去重用户数。"""
    from datetime import timedelta
    from .models import UserBehaviorEvent

    cache_key = f"{CACHE_KEY_PREFIX}behavior_funnel:{days}:{int(timezone.now().timestamp() // CACHE_TTL)}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    now = timezone.now()
    threshold_dt = now - timedelta(days=days)

    events = list(
        UserBehaviorEvent.objects.filter(
            created_at__gte=threshold_dt,
            user__isnull=False,
        ).values("event_name").annotate(
            user_count=Count("user", distinct=True),
            total_count=Count("id"),
        )
    )

    by_name = {row["event_name"]: row for row in events}
    order = [
        UserBehaviorEvent.EventName.LANDING_VIEW,
        UserBehaviorEvent.EventName.CREATION_FORM_OPEN,
        UserBehaviorEvent.EventName.CREATION_SUBMITTED,
        UserBehaviorEvent.EventName.NODE_EDITED,
        UserBehaviorEvent.EventName.SCRIPT_EXPORTED,
        UserBehaviorEvent.EventName.SHARE_LINK_GENERATED,
    ]
    stages = []
    for name in order:
        row = by_name.get(name.value, {"user_count": 0, "total_count": 0})
        stages.append({
            "key": name.value,
            "label": name.label,
            "user_count": row["user_count"],
            "total_count": row["total_count"],
        })

    data = {
        "window_days": days,
        "stages": stages,
    }
    cache.set(cache_key, data, CACHE_TTL)
    return data
