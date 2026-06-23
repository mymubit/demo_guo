# -*- coding: utf-8 -*-
"""
会员模块数据模型
"""
import uuid
from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.billing.commerce_pricing import resolve_charge_price


class MembershipPlan(models.Model):
    """会员套餐"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("套餐名称", max_length=100)
    price = models.DecimalField("价格(元)", max_digits=10, decimal_places=2, default=Decimal("0"))
    original_price = models.DecimalField(
        "划线原价(元)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="可选，用于展示划线价与折扣计算",
    )
    discount_percent = models.DecimalField(
        "折扣(%)",
        max_digits=5,
        decimal_places=2,
        default=Decimal("100"),
        help_text="100 表示无折扣；有划线原价时按 原价×折扣% 计算实付",
    )
    validity_days = models.IntegerField("有效期(天)", default=30)
    creation_quota = models.IntegerField(
        "创作次数配额",
        default=0,
        help_text="遗留字段；商业站以 grant_coins 为准",
    )
    grant_coins = models.PositiveIntegerField(
        "开通赠送币",
        default=0,
        help_text="开通/续费该套餐时发放的网站币",
    )
    features = models.JSONField("套餐特性", default=dict, blank=True)
    is_active = models.BooleanField("是否启用", default=True)
    is_recommended = models.BooleanField("是否推荐", default=False)
    sort_order = models.IntegerField("排序", default=0, help_text="数值越小越靠前")
    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "会员套餐"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return f"{self.name} - ¥{self.price}"

    @property
    def charge_price(self):
        return resolve_charge_price(
            original=self.original_price,
            discount_percent=self.discount_percent,
            manual_price=self.price,
        )

    def clean(self):
        if self.price < 0:
            raise ValidationError({"price": "价格不能为负数"})
        if self.original_price is not None and self.original_price < 0:
            raise ValidationError({"original_price": "划线原价不能为负数"})
        if self.validity_days <= 0:
            raise ValidationError({"validity_days": "有效期必须大于 0"})

    def save(self, *args, **kwargs):
        self.price = self.charge_price
        super().save(*args, **kwargs)


class UserMembership(models.Model):
    """用户会员"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="用户",
    )
    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.PROTECT,
        related_name="user_memberships",
        verbose_name="所属套餐",
    )
    start_at = models.DateTimeField("生效时间", default=timezone.now)
    end_at = models.DateTimeField("到期时间")
    remaining_creations = models.IntegerField("剩余创作次数", default=0)
    is_active = models.BooleanField("是否有效", default=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "用户会员"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["end_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.plan.name}"

    def save(self, *args, **kwargs):
        if not self.end_at:
            self.end_at = self.start_at + timedelta(days=self.plan.validity_days)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        return timezone.now() > self.end_at

    @property
    def has_unlimited_creations(self) -> bool:
        """是否无限创作次数"""
        return self.plan.creation_quota == -1


class PromoCode(models.Model):
    """卡密/兑换码"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField("卡密", max_length=50, unique=True)
    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.PROTECT,
        related_name="promo_codes",
        verbose_name="对应套餐",
    )
    max_uses = models.IntegerField("最大使用次数", default=1)
    used_count = models.IntegerField("已使用次数", default=0)
    expires_at = models.DateTimeField("过期时间")
    is_active = models.BooleanField("是否启用", default=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "卡密兑换码"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.code

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_available(self) -> bool:
        """是否可兑换"""
        return (
            self.is_active
            and not self.is_expired
            and self.used_count < self.max_uses
        )


class MembershipFeatureMatrixItem(models.Model):
    """C 端会员权益对比行（DB 优先，代码默认值兜底）"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature_key = models.CharField("权益键", max_length=64, unique=True)
    label = models.CharField("展示名称", max_length=128)
    free = models.BooleanField("普通用户", default=False)
    member = models.BooleanField("会员", default=True)
    coming_soon = models.BooleanField("即将上线", default=False)
    member_only = models.BooleanField("仅会员", default=False)
    is_active = models.BooleanField("启用", default=True)
    sort_order = models.IntegerField("排序", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "会员权益矩阵"
        verbose_name_plural = verbose_name
        db_table = "membership_feature_matrix_item"
        ordering = ["sort_order", "feature_key"]

    def __str__(self) -> str:
        return self.label
