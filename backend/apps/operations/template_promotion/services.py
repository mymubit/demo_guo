"""模板沉淀服务。"""
from __future__ import annotations

import logging
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.operations.constants import TemplatePromotionStatus
from apps.operations.exceptions import TemplatePromotionError

from .models import TemplatePromotion, TemplatePromotionLog

logger = logging.getLogger(__name__)


@transaction.atomic
def submit_candidate(
    *,
    project=None,
    source_template=None,
    name: str,
    description: str = "",
    category: str = "",
    tags: list | None = None,
    highlights: list | None = None,
    metric_snapshot: dict | None = None,
    operator: str = "",
) -> TemplatePromotion:
    """提交候选模板。"""
    p = TemplatePromotion.objects.create(
        project=project,
        source_template=source_template,
        name=name[:128],
        description=description,
        category=category[:64],
        tags=tags or [],
        highlights=highlights or [],
        metric_snapshot=metric_snapshot or {},
        status=TemplatePromotionStatus.CANDIDATE,
        created_by=operator,
    )
    TemplatePromotionLog.objects.create(
        promotion=p, action="candidate", operator=operator,
        to_status=TemplatePromotionStatus.CANDIDATE,
    )
    return p


@transaction.atomic
def transition(
    promotion: TemplatePromotion,
    *,
    to_status: str,
    operator: str = "",
    note: str = "",
) -> TemplatePromotion:
    valid = {
        TemplatePromotionStatus.CANDIDATE: {TemplatePromotionStatus.REVIEWING, TemplatePromotionStatus.REJECTED},
        TemplatePromotionStatus.REVIEWING: {TemplatePromotionStatus.APPROVED, TemplatePromotionStatus.REJECTED},
        TemplatePromotionStatus.APPROVED: {TemplatePromotionStatus.PUBLISHED, TemplatePromotionStatus.ARCHIVED},
        TemplatePromotionStatus.PUBLISHED: {TemplatePromotionStatus.ARCHIVED},
        TemplatePromotionStatus.REJECTED: {TemplatePromotionStatus.CANDIDATE},
        TemplatePromotionStatus.ARCHIVED: set(),
    }
    if to_status not in valid.get(promotion.status, set()):
        raise TemplatePromotionError(f"非法状态转移：{promotion.status} → {to_status}")
    from_status = promotion.status
    promotion.status = to_status
    if to_status == TemplatePromotionStatus.REVIEWING:
        pass
    elif to_status == TemplatePromotionStatus.APPROVED:
        promotion.reviewed_at = timezone.now()
    elif to_status == TemplatePromotionStatus.PUBLISHED:
        promotion.published_at = timezone.now()
    if note:
        promotion.review_note = note[:1000]
    promotion.save(update_fields=[
        "status", "reviewed_at", "published_at", "review_note", "updated_at",
    ])
    TemplatePromotionLog.objects.create(
        promotion=promotion, action=f"transition_{to_status}",
        operator=operator, from_status=from_status, to_status=to_status, note=note[:500],
    )
    return promotion


def link_promoted_pack(promotion: TemplatePromotion, pack) -> TemplatePromotion:
    """关联上架后的官方 pack。"""
    promotion.promoted_pack = pack
    promotion.save(update_fields=["promoted_pack", "updated_at"])
    return promotion
