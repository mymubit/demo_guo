# -*- coding: utf-8 -*-
"""网站币种、流水、动作定价、主链节点编排（运营配置）。"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.billing.commerce_pricing import resolve_charge_price


class SiteCoinSettings(models.Model):
    """站点币种全局配置（单行）"""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    currency_name = models.CharField("币种名称", max_length=32, default="创作币")
    signup_bonus = models.PositiveIntegerField("注册赠送", default=100)
    default_pipeline_mode = models.CharField(
        "默认创作模式",
        max_length=8,
        choices=[("auto", "一键生成"), ("step", "分步掌控")],
        default="step",
    )
    require_membership_for_creation = models.BooleanField(
        "创作需有效会员",
        default=True,
        help_text="开启后须有效会员才可发起创作（仍按币扣费）",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "站点币种设置"
        verbose_name_plural = verbose_name
        db_table = "billing_site_coin_settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteCoinSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class UserWallet(models.Model):
    """用户钱包"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet",
        verbose_name="用户",
    )
    balance = models.PositiveIntegerField("余额", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "用户钱包"
        verbose_name_plural = verbose_name
        db_table = "billing_user_wallet"

    def __str__(self) -> str:
        return f"{self.user_id} · {self.balance}"


class CoinLedger(models.Model):
    """币种流水（不可改，仅追加）"""

    TYPE_GRANT = "grant"
    TYPE_SPEND = "spend"
    TYPE_REFUND = "refund"
    TYPE_ADJUST = "adjust"
    TYPE_CHOICES = [
        (TYPE_GRANT, "发放"),
        (TYPE_SPEND, "消耗"),
        (TYPE_REFUND, "退还"),
        (TYPE_ADJUST, "人工调整"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coin_ledgers",
        verbose_name="用户",
    )
    delta = models.IntegerField("变动量（负为消耗）")
    balance_after = models.PositiveIntegerField("变动后余额")
    entry_type = models.CharField("类型", max_length=16, choices=TYPE_CHOICES)
    action_key = models.CharField("动作键", max_length=64, blank=True, default="")
    reference_id = models.CharField("关联ID", max_length=64, blank=True, default="")
    remark = models.CharField("备注", max_length=200, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "币种流水"
        verbose_name_plural = verbose_name
        db_table = "billing_coin_ledger"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["action_key"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "action_key", "reference_id"],
                condition=models.Q(delta__gt=0) & ~models.Q(reference_id=""),
                name="uniq_positive_coin_ledger_reference",
            ),
            models.UniqueConstraint(
                fields=["user", "action_key", "reference_id"],
                condition=models.Q(delta__lt=0) & ~models.Q(reference_id=""),
                name="uniq_negative_coin_ledger_reference",
            ),
        ]


class ActionPricing(models.Model):
    """动作扣费定价（后台可配）"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_key = models.CharField("动作键", max_length=64, unique=True)
    display_name = models.CharField("展示名称", max_length=100)
    coin_cost = models.PositiveIntegerField("消耗币数", default=0)
    member_only = models.BooleanField(
        "仅会员可用",
        default=False,
        help_text="开启后须有效会员才可执行该动作",
    )
    is_active = models.BooleanField("启用", default=True)
    sort_order = models.IntegerField("排序", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "动作定价"
        verbose_name_plural = verbose_name
        db_table = "billing_action_pricing"
        ordering = ["sort_order", "action_key"]

    def __str__(self) -> str:
        return f"{self.action_key} · {self.coin_cost}"


class RechargePackage(models.Model):
    """充值档位（人民币 → 创作币）"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("档位名称", max_length=64)
    price_yuan = models.DecimalField("价格（元）", max_digits=10, decimal_places=2)
    base_coins = models.PositiveIntegerField("基础币数", default=0)
    bonus_coins = models.PositiveIntegerField("赠送币数", default=0)
    original_price_yuan = models.DecimalField(
        "划线原价（元）",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="可选，用于展示优惠",
    )
    discount_percent = models.DecimalField(
        "折扣(%)",
        max_digits=5,
        decimal_places=2,
        default=Decimal("100"),
        help_text="100 表示无折扣；有划线原价时按 原价×折扣% 计算实付",
    )
    is_active = models.BooleanField("启用", default=True)
    sort_order = models.PositiveSmallIntegerField("排序", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "充值档位"
        verbose_name_plural = verbose_name
        db_table = "billing_recharge_package"
        ordering = ["sort_order", "price_yuan"]

    @property
    def total_coins(self) -> int:
        return int(self.base_coins) + int(self.bonus_coins)

    @property
    def charge_price(self):
        return resolve_charge_price(
            original=self.original_price_yuan,
            discount_percent=self.discount_percent,
            manual_price=self.price_yuan,
        )

    def save(self, *args, **kwargs):
        self.price_yuan = self.charge_price
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} · ¥{self.price_yuan} → {self.total_coins}币"


class AiFieldPromptConfig(models.Model):
    """表单字段 AI 提示词（与 ActionPricing.action_key 对齐，可后台编辑）"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_key = models.CharField("动作键", max_length=64, unique=True)
    display_name = models.CharField("展示名称", max_length=100, blank=True, default="")
    system_prompt = models.TextField("System 提示词", blank=True, default="")
    user_prompt_tpl = models.TextField(
        "User 模板",
        blank=True,
        default="",
        help_text="可用占位符：{theme} {episode_count} {core_idea} {audience} {reference_work}",
    )
    system_prompt_fallback = models.TextField(
        "备用 System",
        blank=True,
        default="",
        help_text="JSON 模式失败时的文本降级提示词",
    )
    response_json = models.BooleanField("JSON 输出", default=False)
    is_active = models.BooleanField("启用", default=True)
    sort_order = models.IntegerField("排序", default=0)
    llm_provider = models.ForeignKey(
        "skill.LlmProvider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_field_prompts",
        verbose_name="指定大模型",
        help_text="留空则使用全局激活的大模型",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "字段 AI 提示词"
        verbose_name_plural = verbose_name
        db_table = "billing_ai_field_prompt"
        ordering = ["sort_order", "action_key"]

    def __str__(self) -> str:
        return self.action_key
