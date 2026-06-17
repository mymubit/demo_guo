"""创作者激励模型。

业务闭环：
  ① 创作者完成项目 / 模板被使用 → 触发积分入账
  ② 积分累计触发等级晋升 / 勋章解锁
  ③ 创作者用积分兑换权益（创作币 / 会员 / 实物）
  ④ 运营可调整积分（admin_adjust）
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.operations.constants import PointsReason


# ──────────────────────────────────────────────
# 等级
# ──────────────────────────────────────────────

class CreatorLevel(models.Model):
    """创作者等级档位。"""

    code = models.CharField(max_length=32, unique=True, help_text="L1 / L2 / L3 ...")
    name = models.CharField(max_length=64, help_text="见习创作者 / 进阶 / 大神 ...")
    min_points = models.PositiveIntegerField(help_text="累计积分门槛")
    max_points = models.PositiveIntegerField(default=0, help_text="累计积分上限 (0 = 无上限)")
    badge_icon = models.CharField(max_length=256, blank=True, default="")
    benefits = models.JSONField(default=list, help_text="权益说明")
    order = models.IntegerField(default=0, help_text="排序权重")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_creator_level"
        ordering = ["order", "min_points"]


class CreatorProfile(models.Model):
    """创作者档案（每个 user 一条）。"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="creator_profile",
    )
    level = models.ForeignKey(
        CreatorLevel, on_delete=models.SET_NULL,
        related_name="members", null=True, blank=True,
    )
    total_points = models.BigIntegerField(default=0, help_text="累计获得积分（仅入账方向）")
    available_points = models.BigIntegerField(default=0, help_text="可用积分（可用于兑换）")
    used_points = models.BigIntegerField(default=0, help_text="已消耗积分")
    project_count = models.PositiveIntegerField(default=0)
    template_count = models.PositiveIntegerField(default=0)
    badges = models.ManyToManyField(
        "operations_creator.Badge", blank=True, related_name="owners",
    )
    is_certified = models.BooleanField(default=False, help_text="官方认证")
    certified_at = models.DateTimeField(null=True, blank=True)
    bio = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_creator_profile"
        indexes = [
            models.Index(fields=["-total_points"]),
            models.Index(fields=["level", "-total_points"]),
        ]


# ──────────────────────────────────────────────
# 积分
# ──────────────────────────────────────────────

class PointsAccount(models.Model):
    """积分账户（与 CreatorProfile 一对一冗余：方便聚合查询）。"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="points_account",
    )
    balance = models.BigIntegerField(default=0, help_text="当前可用积分")
    total_earned = models.BigIntegerField(default=0)
    total_spent = models.BigIntegerField(default=0)
    frozen = models.BigIntegerField(default=0, help_text="冻结积分（风控 / 争议中）")
    last_change_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_points_account"


class PointsTransaction(models.Model):
    """积分流水（不可变）。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="points_transactions",
    )
    delta = models.BigIntegerField(help_text="正数入账 / 负数消耗")
    reason = models.CharField(max_length=32, choices=PointsReason.choices)
    ref_type = models.CharField(max_length=32, blank=True, default="", help_text="关联对象类型：project / template / ticket ...")
    ref_id = models.CharField(max_length=64, blank=True, default="")
    note = models.CharField(max_length=255, blank=True, default="")
    operator = models.CharField(max_length=64, blank=True, default="", help_text="admin_adjust 时记录运营账号")
    balance_after = models.BigIntegerField(default=0, help_text="操作后余额")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_points_transaction"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["reason", "-created_at"]),
        ]
        ordering = ["-created_at"]


# ──────────────────────────────────────────────
# 勋章
# ──────────────────────────────────────────────

class Badge(models.Model):
    """勋章定义。"""

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True, default="")
    icon_url = models.CharField(max_length=512, blank=True, default="")
    # 解锁规则：用 trigger_event 表达（project_completed_10 / template_use_100 / first_publish 等）
    trigger_event = models.CharField(max_length=64, blank=True, default="")
    trigger_threshold = models.PositiveIntegerField(default=0)
    rarity = models.CharField(max_length=16, default="common", help_text="common / rare / epic / legend")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_badge"
        ordering = ["rarity", "code"]


class CreatorAchievement(models.Model):
    """创作者获得勋章记录。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="achievements",
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="achievements")
    progress = models.PositiveIntegerField(default=100, help_text="达成进度 0-100")
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_creator_achievement"
        unique_together = [("user", "badge")]
        indexes = [models.Index(fields=["user", "-unlocked_at"])]
