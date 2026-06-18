# -*- coding: utf-8 -*-
"""【运营 M2】Project 内容质量统计服务。

对外只暴露三个写入入口，**所有更新必须经过这里**，避免在业务代码里散落
`Project.objects.update(...)`，确保运营 Dashboard 数据一致。

  • record_user_edit(project)   - 用户保存/编辑工作台内容
  • record_final_export(project)- 用户成功下载/导出最终剧本
  • mark_abandoned(project)     - 用户主动放弃
  • detect_and_mark_abandoned() - 7 天未活跃项目的批量弃用标记（运营定时任务）
"""
from __future__ import annotations

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from ..models import Project

logger = logging.getLogger(__name__)

# 7 天未活跃且未完成即视为弃用（一人运营铁律）
ABANDON_DAYS = 7


def record_user_edit(project: Project) -> Project:
    """用户编辑 Project（保存草稿 / 修改节点内容）。"""
    now = timezone.now()
    Project.objects.filter(pk=project.pk).update(
        user_edit_count=project.user_edit_count + 1 if hasattr(project, "user_edit_count") else 1,
        last_edited_at=now,
        # 用户重新活跃 -> 清除弃用标记
        abandoned_at=None,
    )
    project.refresh_from_db(fields=["user_edit_count", "last_edited_at", "abandoned_at"])
    return project


def record_final_export(project: Project) -> Project:
    """用户成功导出最终剧本（任何格式都算 1 次）。"""
    Project.objects.filter(pk=project.pk).update(
        final_export_count=(project.final_export_count or 0) + 1
        if hasattr(project, "final_export_count") else 1,
    )
    project.refresh_from_db(fields=["final_export_count"])
    return project


@transaction.atomic
def mark_abandoned(project: Project) -> Project:
    """用户主动弃用（或系统判定）。"""
    if project.execution_status in {Project.STATUS_COMPLETED}:
        return project
    if project.abandoned_at:
        return project
    project.abandoned_at = timezone.now()
    project.save(update_fields=["abandoned_at", "updated_at"])
    return project


def detect_and_mark_abandoned(*, days: int = ABANDON_DAYS, limit: int = 500) -> int:
    """扫描 7 天未活跃且未完成的项目，批量标记为弃用。

    返回标记数量。设计为幂等（已标记过的会被过滤掉）。
    用于运营 cron / management command 调用。
    """
    from django.db.models import Q

    threshold_dt = timezone.now() - timedelta(days=days)
    qs = Project.objects.filter(
        abandoned_at__isnull=True,
    ).exclude(fusion_status=Project.FUSION_READY).filter(
        Q(last_edited_at__isnull=True, created_at__lt=threshold_dt)
        | Q(last_edited_at__lt=threshold_dt)
    ).order_by("created_at")[:limit]

    project_ids = list(qs.values_list("pk", flat=True))
    if not project_ids:
        return 0
    count = Project.objects.filter(pk__in=project_ids).update(abandoned_at=timezone.now())
    if count:
        logger.info("[Operations] 批量标记弃用项目 %s 个", count)
    return count


def content_quality_summary(days: int = 30) -> dict:
    """运营 M2 看板：内容质量聚合。"""
    from django.db.models import Count, Q
    from django.utils import timezone

    now = timezone.now()
    threshold_dt = now - timedelta(days=days)

    base = Project.objects.filter(created_at__gte=threshold_dt)
    total = base.count()
    exported = base.filter(final_export_count__gt=0).count()
    edited = base.filter(user_edit_count__gt=0).count()
    abandoned = base.filter(abandoned_at__isnull=False).count()
    completed = base.filter(fusion_status=Project.FUSION_READY).count()
    failed = base.filter(fusion_status=Project.FUSION_BLOCKED).count()

    return {
        "window_days": days,
        "total_projects": total,
        "completed_count": completed,
        "failed_count": failed,
        "abandoned_count": abandoned,
        "edited_count": edited,
        "exported_count": exported,
        "save_rate": round(edited / total * 100, 2) if total else 0.0,
        "export_rate": round(exported / total * 100, 2) if total else 0.0,
        "complete_rate": round(completed / total * 100, 2) if total else 0.0,
        "abandon_rate": round(abandoned / total * 100, 2) if total else 0.0,
    }


def content_quality_funnel(days: int = 30) -> dict:
    """用户漏斗：注册 → 进入创作 → 提交创作 → 至少保存 1 次 → 完成 → 导出。"""
    from datetime import timedelta
    from django.db.models import Count
    from django.utils import timezone

    from apps.users.models import User

    now = timezone.now()
    threshold_dt = now - timedelta(days=days)
    period_projects = Project.objects.filter(created_at__gte=threshold_dt)

    total_projects = period_projects.count()
    submitted = total_projects  # 提交即创建
    saved = period_projects.filter(user_edit_count__gt=0).count()
    completed = period_projects.filter(fusion_status=Project.FUSION_READY).count()
    exported = period_projects.filter(final_export_count__gt=0).count()
    abandoned = period_projects.filter(abandoned_at__isnull=False).count()

    return {
        "window_days": days,
        "submitted": submitted,
        "saved": saved,
        "completed": completed,
        "exported": exported,
        "abandoned": abandoned,
        "stages": [
            {"key": "submitted", "label": "提交创作", "count": submitted, "rate": 100.0 if submitted else 0.0},
            {"key": "saved", "label": "至少保存 1 次", "count": saved,
             "rate": round(saved / submitted * 100, 2) if submitted else 0.0},
            {"key": "completed", "label": "完成创作", "count": completed,
             "rate": round(completed / submitted * 100, 2) if submitted else 0.0},
            {"key": "exported", "label": "成功导出", "count": exported,
             "rate": round(exported / submitted * 100, 2) if submitted else 0.0},
        ],
    }


def stuck_projects(days: int = 3, limit: int = 50) -> list[dict]:
    """卡点人群：>= days 天未完成 + 未弃用 + 有过编辑但未完成的项目。"""
    from django.utils import timezone
    from datetime import timedelta

    threshold_dt = timezone.now() - timedelta(days=days)
    qs = Project.objects.filter(
        fusion_status__in=[
            Project.FUSION_DRAFT,
            Project.FUSION_PLANNING,
            Project.FUSION_WRITING,
            Project.FUSION_REVIEWING,
            Project.FUSION_SCORING,
        ],
        abandoned_at__isnull=True,
        created_at__lt=threshold_dt,
    ).order_by("created_at")[:limit]

    out = []
    for p in qs:
        out.append({
            "project_id": str(p.id),
            "user_id": str(p.user_id) if p.user_id else "",
            "title": (p.title or p.theme or "未命名")[:200],
            "theme": p.theme,
            "status": p.execution_status,
            "status_text": p.get_status_display(),
            "progress_percent": p.progress_percent,
            "user_edit_count": p.user_edit_count,
            "last_edited_at": p.last_edited_at.isoformat() if p.last_edited_at else "",
            "created_at": p.created_at.isoformat() if p.created_at else "",
            "days_since_create": (timezone.now() - p.created_at).days if p.created_at else 0,
        })
    return out
