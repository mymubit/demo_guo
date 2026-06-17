"""运营活动模型。

设计要点：
  ① Campaign：活动容器，定义活动期间、规则、目标人群
  ② CouponTemplate：卡券模板（一个活动可关联多个）
  ③ UserCoupon：用户领取的卡券实例（含有效期、状态）
  ④ RedemptionCodeBatch + RedemptionCode：兑换码批次与码值
  ⑤ CouponClaimLog：领取审计（防刷、风控）
  ⑥ UserCoinLedger 复用，不在本模块重复建账
"""
from __future__ import annotations

import secrets
import string

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.operations.constants import (
    CampaignStatus,
    CampaignType,
    CouponStatus,
    CouponType,
    RedemptionCodeStatus,
)


def _generate_redemption_code(length: int = 12) -> str:
    """生成兑换码（大写字母+数字，去除易混字符 O/0/I/1）。"""
    alphabet = "".join(c for c in (string.ascii_uppercase + string.digits) if c not in "OI01")
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Campaign(models.Model):
    """运营活动。"""

    slug = models.SlugField(max_length=64, unique=True, help_text="活动唯一标识")
    name = models.CharField(max_length=128)
    campaign_type = models.CharField(
        max_length=32, choices=CampaignType.choices, default=CampaignType.LIMITED,
    )
    status = models.CharField(
        max_length=16, choices=CampaignStatus.choices, default=CampaignStatus.DRAFT,
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    description = models.TextField(blank=True, default="")
    rules = models.JSONField(default=dict, help_text="活动规则：触发条件、目标人群、奖励等")
    target_user_filter = models.JSONField(default=dict, help_text="目标用户过滤：vip_level / tags / register_after 等")
    max_claim_per_user = models.PositiveIntegerField(default=1, help_text="单用户最多领取次数")
    total_quota = models.PositiveIntegerField(default=0, help_text="活动总配额（0=无限制）")
    claimed_count = models.PositiveIntegerField(default=0, help_text="已领取总数")
    created_by = models.CharField(max_length=64, blank=True, default="")
    operator = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_campaign"
        indexes = [
            models.Index(fields=["status", "-start_at"]),
            models.Index(fields=["campaign_type", "status"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"[{self.campaign_type}] {self.name}"

    def is_active_window(self) -> bool:
        now = timezone.now()
        return self.start_at <= now < self.end_at

    def has_quota(self) -> bool:
        return self.total_quota <= 0 or self.claimed_count < self.total_quota

    def is_claimable(self) -> bool:
        return self.status == CampaignStatus.RUNNING and self.is_active_window() and self.has_quota()


class CouponTemplate(models.Model):
    """卡券模板（活动可关联多个）。"""

    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="coupon_templates",
        null=True, blank=True,
    )
    name = models.CharField(max_length=128)
    coupon_type = models.CharField(max_length=24, choices=CouponType.choices)
    value = models.DecimalField(max_digits=12, decimal_places=2, help_text="面值（币/Token/折扣率）")
    min_spend = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="最低消费门槛（0=无门槛）",
    )
    valid_days = models.PositiveIntegerField(default=30, help_text="领取后有效天数")
    total_quota = models.PositiveIntegerField(default=0, help_text="0=无限制")
    issued_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=16, choices=CouponStatus.choices, default=CouponStatus.ACTIVE,
    )
    scope = models.JSONField(
        default=dict, help_text="适用范围：membership_levels / skill_ids / categories",
    )
    extra = models.JSONField(default=dict, help_text="扩展：会员试用天数 / 权益内容等")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_coupon_template"
        indexes = [models.Index(fields=["status", "coupon_type"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name}({self.get_coupon_type_display()})"


class UserCoupon(models.Model):
    """用户领取的卡券实例。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_coupons",
    )
    template = models.ForeignKey(CouponTemplate, on_delete=models.PROTECT, related_name="user_coupons")
    campaign = models.ForeignKey(
        Campaign, on_delete=models.SET_NULL, related_name="user_coupons", null=True, blank=True,
    )
    code = models.CharField(max_length=64, unique=True, help_text="卡券实例编码")
    status = models.CharField(
        max_length=16,
        choices=[
            ("unused", "未使用"),
            ("used", "已使用"),
            ("expired", "已过期"),
            ("revoked", "已回收"),
        ],
        default="unused",
    )
    value_snapshot = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="领取时的面值快照（防止模板后续修改）",
    )
    min_spend_snapshot = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    claim_source = models.CharField(max_length=64, default="campaign", help_text="campaign/redemption/admin")
    redemption_code = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_user_coupon"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["valid_to"]),
        ]

    def is_valid(self) -> bool:
        now = timezone.now()
        return self.status == "unused" and self.valid_from <= now < self.valid_to


class RedemptionCodeBatch(models.Model):
    """兑换码批次。"""

    campaign = models.ForeignKey(
        Campaign, on_delete=models.SET_NULL, related_name="code_batches", null=True, blank=True,
    )
    template = models.ForeignKey(
        CouponTemplate, on_delete=models.PROTECT, related_name="code_batches",
    )
    name = models.CharField(max_length=128)
    code_length = models.PositiveIntegerField(default=12)
    total_count = models.PositiveIntegerField()
    issued_count = models.PositiveIntegerField(default=0, help_text="已生成码数")
    claimed_count = models.PositiveIntegerField(default=0, help_text="已领取数")
    prefix = models.CharField(max_length=8, blank=True, default="")
    note = models.TextField(blank=True, default="")
    operator = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_redemption_batch"
        indexes = [models.Index(fields=["-created_at"])]


class RedemptionCode(models.Model):
    """单个兑换码。"""

    batch = models.ForeignKey(
        RedemptionCodeBatch, on_delete=models.CASCADE, related_name="codes",
    )
    code = models.CharField(max_length=32, unique=True)
    status = models.CharField(
        max_length=16, choices=RedemptionCodeStatus.choices,
        default=RedemptionCodeStatus.UNCLAIMED,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name="claimed_redemption_codes", null=True, blank=True,
    )
    user_coupon = models.OneToOneField(
        UserCoupon, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="source_redemption_code",
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_redemption_code"
        indexes = [
            models.Index(fields=["batch", "status"]),
            models.Index(fields=["status", "claimed_at"]),
        ]


class CouponClaimLog(models.Model):
    """卡券领取审计日志。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coupon_claim_logs",
        null=True, blank=True,
    )
    campaign = models.ForeignKey(
        Campaign, on_delete=models.SET_NULL, null=True, blank=True,
    )
    template = models.ForeignKey(
        CouponTemplate, on_delete=models.SET_NULL, null=True, blank=True,
    )
    user_coupon = models.ForeignKey(
        UserCoupon, on_delete=models.SET_NULL, null=True, blank=True,
    )
    claim_source = models.CharField(max_length=64)
    result = models.CharField(max_length=16, help_text="success/duplicate/exhausted/expired/blocked")
    reason = models.CharField(max_length=255, blank=True, default="")
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_coupon_claim_log"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["result", "-created_at"]),
        ]
