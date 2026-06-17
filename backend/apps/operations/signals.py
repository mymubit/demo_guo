"""运营中心信号注册。

本文件只做"轻联动"：把核心域的信号（项目完成、模板被用）
桥接到运营域（积分 / UGC 使用计数）。

⚠️ 不在这里写复杂业务逻辑；业务都在 services.py。
"""
from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 项目完成 → 积分入账
# ──────────────────────────────────────────────

@receiver(post_save, sender="creation.Project")
def _on_project_saved(sender, instance, created, **kwargs):
    """项目状态变更为 'completed' 时触发积分入账（按 ref_id 防重）。"""
    try:
        if getattr(instance, "status", "") != "completed":
            return
        owner = getattr(instance, "owner", None)
        if not owner:
            return
        from apps.operations.creator.models import (
            CreatorProfile,
            PointsReason,
            PointsTransaction,
        )
        from apps.operations.creator import services as creator_services
        if PointsTransaction.objects.filter(
            user=owner,
            reason=PointsReason.PROJECT_COMPLETED,
            ref_type="project",
            ref_id=str(instance.pk),
        ).exists():
            return
        creator_services.auto_grant_for_event(
            user=owner, reason=PointsReason.PROJECT_COMPLETED,
            ref_type="project", ref_id=str(instance.pk),
        )
        # 同步 profile.project_count
        completed_n = instance.__class__.objects.filter(owner=owner, status="completed").count()
        CreatorProfile.objects.filter(user=owner).update(project_count=completed_n)
    except Exception as e:  # pragma: no cover
        logger.warning("operations.signal.project_completed failed: %s", e)


# ──────────────────────────────────────────────
# UGC 模板被使用 → use 计数 + 创作者积分
# ──────────────────────────────────────────────

@receiver(post_save, sender="creation.WorkspaceNode")
def _on_workspace_node_saved(sender, instance, created, **kwargs):
    """WorkspaceNode 关联到 UGC 模板时：记一次 use_count。

    字段约定：extra / payload 里带 {"ugc_template_id": "..."}。
    """
    try:
        if not created:
            return
        payload = getattr(instance, "extra", None) or {}
        if not isinstance(payload, dict):
            return
        template_id = payload.get("ugc_template_id")
        if not template_id:
            return
        from apps.operations.ugc.models import UserTemplate
        from apps.operations.ugc import services as ugc_services
        from apps.operations.creator import services as creator_services
        from apps.operations.constants import PointsReason
        try:
            tpl = UserTemplate.objects.get(pk=template_id)
        except UserTemplate.DoesNotExist:
            return
        ugc_services.record_use(template=tpl)
        creator_services.auto_grant_for_event(
            user=tpl.author, reason=PointsReason.TEMPLATE_USED,
            ref_type="user_template", ref_id=str(tpl.pk),
        )
    except Exception as e:  # pragma: no cover
        logger.warning("operations.signal.ugc_use failed: %s", e)
