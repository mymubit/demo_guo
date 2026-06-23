# -*- coding: utf-8 -*-
"""【运营 M2】Project 内容质量统计服务（Drama SSOT）。"""
from __future__ import annotations

import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..models import Project

logger = logging.getLogger(__name__)

ABANDON_DAYS = 7


def _deliverable_project_ids():
    from apps.drama.progress_service import DramaProgressService

    return list(DramaProgressService.deliverable_project_ids())


def _blocked_project_ids():
    from apps.drama.progress_service import DramaProgressService

    return list(DramaProgressService.blocked_project_ids())


def record_user_edit(project: Project) -> Project:
    """用户编辑 Project（保存草稿 / 修改节点内容）。"""
    now = timezone.now()
    Project.objects.filter(pk=project.pk).update(
        user_edit_count=project.user_edit_count + 1 if hasattr(project, "user_edit_count") else 1,
        last_edited_at=now,
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
    """扫描 N 天未活跃且未交付的项目，批量标记为弃用。"""
    threshold_dt = timezone.now() - timedelta(days=days)
    deliverable = _deliverable_project_ids()
    qs = Project.objects.filter(
        abandoned_at__isnull=True,
    ).exclude(id__in=deliverable).filter(
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
    now = timezone.now()
    threshold_dt = now - timedelta(days=days)

    base = Project.objects.filter(created_at__gte=threshold_dt)
    deliverable = _deliverable_project_ids()
    blocked = _blocked_project_ids()
    total = base.count()
    exported = base.filter(final_export_count__gt=0).count()
    edited = base.filter(user_edit_count__gt=0).count()
    abandoned = base.filter(abandoned_at__isnull=False).count()
    completed = base.filter(id__in=deliverable).count()
    failed = base.filter(id__in=blocked).count()

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
    """用户漏斗：提交 → 保存 → 交付 → 导出。"""
    now = timezone.now()
    threshold_dt = now - timedelta(days=days)
    period_projects = Project.objects.filter(created_at__gte=threshold_dt)
    deliverable = _deliverable_project_ids()

    total_projects = period_projects.count()
    submitted = total_projects
    saved = period_projects.filter(user_edit_count__gt=0).count()
    completed = period_projects.filter(id__in=deliverable).count()
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
    """卡点人群：>= days 天未交付 + 未弃用。"""
    from apps.drama.constants import DramaStage, DramaTrackMode

    threshold_dt = timezone.now() - timedelta(days=days)
    deliverable = set(_deliverable_project_ids())
    drama_pids = Project.objects.filter(
        track_mode__in=[DramaTrackMode.FAST, DramaTrackMode.EXPERT],
    ).exclude(
        Q(delivery_status__in=("ready", "delivered"))
        | Q(drama_stage=DramaStage.DELIVERED)
    ).values_list("id", flat=True)

    qs = Project.objects.filter(
        id__in=drama_pids,
        abandoned_at__isnull=True,
        created_at__lt=threshold_dt,
    ).order_by("created_at")[:limit]

    out = []
    for p in qs:
        if p.id in deliverable:
            continue
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
