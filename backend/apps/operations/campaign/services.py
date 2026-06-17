"""运营活动服务（精简版）。

提供：Campaign CRUD、Coupon CRUD、批量生成兑换码、起停活动。
不做：领取流水、风控审计、跨活动跨用户配额。
"""
from __future__ import annotations

import logging
import secrets
import string
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.operations.constants import CampaignStatus
from apps.operations.exceptions import OpsError

from .models import Campaign, Coupon, RedemptionCode

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Campaign
# ──────────────────────────────────────────────

@transaction.atomic
def create_campaign(*, name: str, description: str = "", start_at=None, end_at=None, note: str = "") -> Campaign:
    c = Campaign.objects.create(
        name=name[:128],
        description=description,
        start_at=start_at or timezone.now(),
        end_at=end_at or (timezone.now() + timedelta(days=30)),
        note=note[:255],
    )
    return c


@transaction.atomic
def update_campaign(campaign: Campaign, **fields) -> Campaign:
    for k in ("name", "description", "start_at", "end_at", "note", "status"):
        if k in fields and fields[k] is not None:
            setattr(campaign, k, fields[k])
    campaign.save()
    return campaign


@transaction.atomic
def start_campaign(campaign: Campaign) -> Campaign:
    campaign.status = CampaignStatus.RUNNING
    campaign.save(update_fields=["status", "updated_at"])
    return campaign


@transaction.atomic
def pause_campaign(campaign: Campaign) -> Campaign:
    campaign.status = CampaignStatus.PAUSED
    campaign.save(update_fields=["status", "updated_at"])
    return campaign


@transaction.atomic
def end_campaign(campaign: Campaign) -> Campaign:
    campaign.status = CampaignStatus.ENDED
    campaign.save(update_fields=["status", "updated_at"])
    return campaign


# ──────────────────────────────────────────────
# Coupon
# ──────────────────────────────────────────────

@transaction.atomic
def create_coupon(*, campaign: Campaign, name: str, coupon_type: str,
                  value=0, valid_days: int = 30, total_quota: int = 0) -> Coupon:
    return Coupon.objects.create(
        campaign=campaign,
        name=name[:128],
        coupon_type=coupon_type,
        value=value,
        valid_days=valid_days,
        total_quota=total_quota,
    )


@transaction.atomic
def toggle_coupon(coupon: Coupon, *, is_active: bool) -> Coupon:
    coupon.is_active = is_active
    coupon.save(update_fields=["is_active", "updated_at"])
    return coupon


# ──────────────────────────────────────────────
# Redemption Codes
# ──────────────────────────────────────────────

def _gen_code(length: int = 10) -> str:
    alphabet = "".join(c for c in (string.ascii_uppercase + string.digits) if c not in "OI01")
    return "".join(secrets.choice(alphabet) for _ in range(length))


@transaction.atomic
def generate_codes(coupon: Coupon, *, count: int, expires_at=None) -> int:
    """批量生成兑换码，返回实际生成数。"""
    if count <= 0 or count > 10000:
        raise OpsError("单次生成数量需在 1-10000 之间")
    # 检查配额
    if coupon.total_quota > 0 and coupon.claimed_count + count > coupon.total_quota:
        raise OpsError(f"超过卡券总配额（已发 {coupon.claimed_count} / 总 {coupon.total_quota}）")
    objs = [
        RedemptionCode(coupon=coupon, code=_gen_code(), expires_at=expires_at)
        for _ in range(count)
    ]
    RedemptionCode.objects.bulk_create(objs, batch_size=500)
    coupon.claimed_count = coupon.claimed_count + count
    coupon.save(update_fields=["claimed_count", "updated_at"])
    logger.info("campaign.generate_codes coupon=%s count=%s", coupon.pk, count)
    return count
