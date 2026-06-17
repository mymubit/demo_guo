"""运营活动模型（精简版）。

个人站够用即可：
  - Campaign：活动
  - Coupon：每个活动下面挂的卡券（一个活动可多张）
  - RedemptionCode：兑换码（直接关联 Coupon，不拆 Batch）
  - 不做 ClaimLog / 风控审计 / 多模板规则
"""
from __future__ import annotations

import secrets
import string

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.operations.constants import CampaignStatus, CouponType


def _gen_code(length: int = 10) -> str:
    """生成兑换码（去掉 O/0/I/1 易混字符）。"""
    alphabet = "".join(c for c in (string.ascii_uppercase + string.digits) if c not in "OI01")
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Campaign(models.Model):
    """运营活动。"""

    name = models.CharField(max_length=128)
    status = models.CharField(max_length=16, choices=CampaignStatus.choices, default=CampaignStatus.DRAFT)
    start_at = models.DateTimeField(default=timezone.now)
    end_at = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, default="")
    note = models.CharField(max_length=255, blank=True, default="", help_text="给自己看的备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_campaign"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-start_at"])]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Coupon(models.Model):
    """活动下挂的卡券（直接发或生成兑换码）。"""

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="coupons")
    name = models.CharField(max_length=128)
    coupon_type = models.CharField(max_length=16, choices=CouponType.choices, default=CouponType.COIN)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="面值（币/折扣率）")
    valid_days = models.PositiveIntegerField(default=30)
    total_quota = models.PositiveIntegerField(default=0, help_text="0=不限")
    claimed_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_coupon"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} ({self.campaign.name})"


class RedemptionCode(models.Model):
    """兑换码。直接归属 Coupon，码生成后存这里。"""

    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="codes")
    code = models.CharField(max_length=32, unique=True)
    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="redeemed_codes",
    )
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_redemption_code"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["coupon", "is_used"])]
