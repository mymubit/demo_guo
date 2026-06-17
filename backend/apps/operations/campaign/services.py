"""运营活动服务层。"""
from __future__ import annotations

import logging
import secrets
import string
from datetime import timedelta
from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from apps.operations.constants import (
    CampaignStatus,
    CouponStatus,
    RedemptionCodeStatus,
)
from apps.operations.exceptions import (
    CampaignNotRunning,
    CouponAlreadyClaimed,
    CouponExhausted,
    CouponExpired,
    RedemptionCodeInvalid,
)

from .models import (
    Campaign,
    CouponClaimLog,
    CouponTemplate,
    RedemptionCode,
    RedemptionCodeBatch,
    UserCoupon,
)

logger = logging.getLogger(__name__)


def _gen_coupon_code() -> str:
    """生成用户卡券实例编码。"""
    alphabet = string.ascii_uppercase + string.digits
    return "CP" + "".join(secrets.choice(alphabet) for _ in range(12))


def _gen_redemption_code(length: int = 12, prefix: str = "") -> str:
    alphabet = "".join(c for c in (string.ascii_uppercase + string.digits) if c not in "OI01")
    code = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}{code}" if prefix else code


# ──────────────────────────────────────────────
# Campaign 生命周期
# ──────────────────────────────────────────────
def activate_campaign(campaign_id: int, operator: str = "") -> Campaign:
    """启动活动。"""
    campaign = Campaign.objects.get(id=campaign_id)
    if not campaign.is_active_window():
        raise CampaignNotRunning("活动不在有效期内")
    campaign.status = CampaignStatus.RUNNING
    campaign.operator = operator or campaign.operator
    campaign.save(update_fields=["status", "operator", "updated_at"])
    return campaign


def pause_campaign(campaign_id: int, operator: str = "") -> Campaign:
    campaign = Campaign.objects.get(id=campaign_id)
    campaign.status = CampaignStatus.PAUSED
    campaign.operator = operator
    campaign.save(update_fields=["status", "operator", "updated_at"])
    return campaign


def end_campaign(campaign_id: int, operator: str = "") -> Campaign:
    campaign = Campaign.objects.get(id=campaign_id)
    campaign.status = CampaignStatus.ENDED
    campaign.operator = operator
    campaign.save(update_fields=["status", "operator", "updated_at"])
    return campaign


# ──────────────────────────────────────────────
# 领取卡券
# ──────────────────────────────────────────────
@transaction.atomic
def claim_coupon(
    user,
    *,
    campaign_id: int | None = None,
    template_id: int | None = None,
    claim_source: str = "campaign",
    redemption_code: str = "",
    ip: str = "",
    user_agent: str = "",
) -> UserCoupon:
    """用户领取一张卡券。

    支持两种入口：
      A. campaign 领取：从活动下未领完的模板中领一张
      B. 兑换码领取：通过 redemption_code 兑换指定模板
    """
    if campaign_id:
        return _claim_from_campaign(
            user=user,
            campaign_id=campaign_id,
            claim_source=claim_source,
            ip=ip,
            user_agent=user_agent,
        )
    if template_id and redemption_code:
        return _claim_from_redemption_code(
            user=user,
            template_id=template_id,
            code=redemption_code,
            ip=ip,
            user_agent=user_agent,
        )
    raise CampaignNotRunning("缺少活动或兑换码参数")


def _claim_from_campaign(
    user, *, campaign_id: int, claim_source: str, ip: str, user_agent: str,
) -> UserCoupon:
    campaign = Campaign.objects.select_for_update().get(id=campaign_id)
    if not campaign.is_claimable():
        if campaign.status != CampaignStatus.RUNNING:
            raise CampaignNotRunning(f"活动当前状态：{campaign.get_status_display()}")
        if not campaign.is_active_window():
            raise CouponExpired("活动不在有效期内")
        if not campaign.has_quota():
            raise CouponExhausted("活动已发完")
        raise CampaignNotRunning("活动不可领取")

    # 单用户领取次数校验
    already = UserCoupon.objects.filter(
        user=user, campaign=campaign,
    ).count()
    if already >= campaign.max_claim_per_user:
        CouponClaimLog.objects.create(
            user=user, campaign=campaign, claim_source=claim_source,
            result="duplicate", reason="max_per_user_reached", ip=ip, user_agent=user_agent,
        )
        raise CouponAlreadyClaimed(f"单用户最多领取 {campaign.max_claim_per_user} 张")

    # 选一张可选模板：未超额 + ACTIVE
    candidates = CouponTemplate.objects.select_for_update().filter(
        campaign=campaign, status=CouponStatus.ACTIVE,
    )
    template = None
    for cand in candidates:
        if cand.total_quota <= 0 or cand.issued_count < cand.total_quota:
            template = cand
            break
    if template is None:
        CouponClaimLog.objects.create(
            user=user, campaign=campaign, claim_source=claim_source,
            result="exhausted", reason="no_template_available", ip=ip, user_agent=user_agent,
        )
        raise CouponExhausted("活动无可用卡券")

    now = timezone.now()
    user_coupon = UserCoupon.objects.create(
        user=user,
        template=template,
        campaign=campaign,
        code=_gen_coupon_code(),
        value_snapshot=template.value,
        min_spend_snapshot=template.min_spend,
        valid_from=now,
        valid_to=now + timedelta(days=template.valid_days),
        claim_source=claim_source,
    )
    CouponTemplate.objects.filter(id=template.id).update(issued_count=F("issued_count") + 1)
    Campaign.objects.filter(id=campaign.id).update(claimed_count=F("claimed_count") + 1)
    CouponClaimLog.objects.create(
        user=user, campaign=campaign, template=template, user_coupon=user_coupon,
        claim_source=claim_source, result="success", ip=ip, user_agent=user_agent,
    )
    return user_coupon


def _claim_from_redemption_code(
    user, *, template_id: int, code: str, ip: str, user_agent: str,
) -> UserCoupon:
    try:
        rc = RedemptionCode.objects.select_for_update().get(code=code, batch__template_id=template_id)
    except RedemptionCode.DoesNotExist as e:
        raise RedemptionCodeInvalid("兑换码无效") from e
    if rc.status == RedemptionCodeStatus.CLAIMED:
        raise RedemptionCodeInvalid("兑换码已被领取")
    if rc.status == RedemptionCodeStatus.DISABLED:
        raise RedemptionCodeInvalid("兑换码已作废")
    if rc.expires_at and rc.expires_at < timezone.now():
        rc.status = RedemptionCodeStatus.EXPIRED
        rc.save(update_fields=["status", "updated_at"])
        raise RedemptionCodeInvalid("兑换码已过期")

    template = CouponTemplate.objects.get(id=template_id)
    now = timezone.now()
    user_coupon = UserCoupon.objects.create(
        user=user,
        template=template,
        campaign=rc.batch.campaign,
        code=_gen_coupon_code(),
        value_snapshot=template.value,
        min_spend_snapshot=template.min_spend,
        valid_from=now,
        valid_to=now + timedelta(days=template.valid_days),
        claim_source="redemption",
        redemption_code=code,
    )
    RedemptionCodeBatch.objects.filter(id=rc.batch_id).update(claimed_count=F("claimed_count") + 1)
    rc.status = RedemptionCodeStatus.CLAIMED
    rc.user = user
    rc.user_coupon = user_coupon
    rc.claimed_at = now
    rc.save(update_fields=["status", "user", "user_coupon", "claimed_at", "updated_at"])
    CouponClaimLog.objects.create(
        user=user, campaign=rc.batch.campaign, template=template, user_coupon=user_coupon,
        claim_source="redemption", result="success", redemption_code=code, ip=ip, user_agent=user_agent,
    )
    return user_coupon


# ──────────────────────────────────────────────
# 兑换码生成
# ──────────────────────────────────────────────
@transaction.atomic
def generate_redemption_codes(
    *,
    template_id: int,
    count: int,
    operator: str = "",
    name: str = "",
    prefix: str = "",
    code_length: int = 12,
    campaign_id: int | None = None,
    expires_at: Any = None,
) -> RedemptionCodeBatch:
    """批量生成兑换码（分批写入，避免长事务）。"""
    template = CouponTemplate.objects.get(id=template_id)
    if count <= 0 or count > 100_000:
        raise ValueError("count 必须在 1~100000")
    batch = RedemptionCodeBatch.objects.create(
        campaign_id=campaign_id,
        template=template,
        name=name or f"批次-{timezone.now().strftime('%Y%m%d-%H%M%S')}",
        code_length=code_length,
        total_count=count,
        prefix=prefix or "",
        operator=operator,
    )
    objs: list[RedemptionCode] = []
    seen: set[str] = set()
    while len(objs) < count:
        code = _gen_redemption_code(code_length, prefix)
        if code in seen:
            continue
        seen.add(code)
        objs.append(RedemptionCode(
            batch=batch, code=code, expires_at=expires_at,
            status=RedemptionCodeStatus.UNCLAIMED,
        ))
        if len(objs) >= 1000:
            RedemptionCode.objects.bulk_create(objs, batch_size=500, ignore_conflicts=True)
            objs.clear()
    if objs:
        RedemptionCode.objects.bulk_create(objs, batch_size=500, ignore_conflicts=True)
    RedemptionCodeBatch.objects.filter(id=batch.id).update(issued_count=count)
    return batch


# ──────────────────────────────────────────────
# 查询
# ──────────────────────────────────────────────
def get_user_coupons(user, *, include_expired: bool = False) -> list[UserCoupon]:
    qs = UserCoupon.objects.filter(user=user).select_related("template", "campaign").order_by("-created_at")
    if not include_expired:
        qs = qs.exclude(valid_to__lt=timezone.now())
    return list(qs)

