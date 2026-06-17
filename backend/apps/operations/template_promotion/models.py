"""模板沉淀模型。

业务闭环：
  ① 优质 project → 运营标记为"候选模板"
  ② 模板沉淀审核人（内容运营）审核通过
  ③ 转化为官方 FusionPipelinePack（带 version + display_name）
  ④ 上架到推荐位 / 主题模板库
  ⑤ 持续跟踪使用率、复刻率、贡献度
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.operations.constants import TemplatePromotionStatus


class TemplatePromotion(models.Model):
    """爆款模板沉淀。"""

    project = models.ForeignKey(
        "creation.Project", on_delete=models.CASCADE, related_name="promotions",
        null=True, blank=True,
    )
    source_template = models.ForeignKey(
        "workflow.FusionPipelinePack", on_delete=models.SET_NULL,
        related_name="promotions", null=True, blank=True,
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=64, blank=True, default="")
    tags = models.JSONField(default=list, help_text="标签：爆款 / 24集 / 逆袭 / 高分 等")
    cover_url = models.CharField(max_length=512, blank=True, default="")
    highlights = models.JSONField(default=list, help_text="亮点：节奏快 / 反转密 / 强情绪 等")
    metric_snapshot = models.JSONField(default=dict, help_text="指标快照：完读率 / 评分 / 收藏数 等")
    status = models.CharField(
        max_length=16, choices=TemplatePromotionStatus.choices,
        default=TemplatePromotionStatus.CANDIDATE,
    )
    promoted_pack = models.ForeignKey(
        "workflow.FusionPipelinePack", on_delete=models.SET_NULL,
        related_name="promoted_from", null=True, blank=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name="reviewed_promotions", null=True, blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_template_promotion"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["category", "status"]),
        ]
        ordering = ["-created_at"]


class TemplatePromotionLog(models.Model):
    """沉淀操作流水。"""

    promotion = models.ForeignKey(TemplatePromotion, on_delete=models.CASCADE, related_name="logs")
    action = models.CharField(max_length=32, help_text="candidate / review / approve / reject / publish / archive")
    operator = models.CharField(max_length=64, blank=True, default="")
    from_status = models.CharField(max_length=32, blank=True, default="")
    to_status = models.CharField(max_length=32, blank=True, default="")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_template_promotion_log"
        indexes = [models.Index(fields=["promotion", "-created_at"])]
        ordering = ["-created_at"]
