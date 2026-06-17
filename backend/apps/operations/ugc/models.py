"""UGC 模板市场模型。

业务闭环：
  ① 用户（创作者）将 project / pack 快照打包为 UGC 模板
  ② 提交审核 → 运营审核通过 → 发布
  ③ 其他用户浏览/搜索 → 评分/收藏/下载/使用
  ④ 自动累计下载量、评分分布，给创作者发激励
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.operations.constants import UgcTemplateStatus


class UserTemplate(models.Model):
    """用户发布的 UGC 模板。"""

    slug = models.SlugField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=64, blank=True, default="")
    tags = models.JSONField(default=list, help_text="标签：甜宠 / 悬疑 / 高反转 等")
    cover_url = models.CharField(max_length=512, blank=True, default="")

    # 快照：发布时锁定的 pack 配置（解耦 pack 下架 / 修改）
    pack_snapshot = models.JSONField(
        default=dict,
        help_text="包快照：nodes / edges / runner_path / skill_id 列表",
    )
    source_pack = models.ForeignKey(
        "workflow.FusionPipelinePack", on_delete=models.SET_NULL,
        related_name="ugc_clones", null=True, blank=True,
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="ugc_templates",
    )

    status = models.CharField(
        max_length=16, choices=UgcTemplateStatus.choices,
        default=UgcTemplateStatus.DRAFT,
    )
    review_note = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name="reviewed_ugc_templates", null=True, blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # 统计字段（写时累加）
    downloads_count = models.PositiveIntegerField(default=0)
    uses_count = models.PositiveIntegerField(default=0)
    rating_count = models.PositiveIntegerField(default=0)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    collection_count = models.PositiveIntegerField(default=0)

    is_featured = models.BooleanField(default=False, help_text="运营置顶")
    sort_weight = models.IntegerField(default=0, help_text="运营人工排序权重")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_user_template"
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["author", "status"]),
            models.Index(fields=["-downloads_count"]),
        ]
        ordering = ["-is_featured", "-sort_weight", "-published_at"]


class UserTemplateRating(models.Model):
    """用户评分。"""

    template = models.ForeignKey(
        UserTemplate, on_delete=models.CASCADE, related_name="ratings",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="ugc_ratings",
    )
    score = models.PositiveSmallIntegerField(help_text="1-5 星")
    comment = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_user_template_rating"
        unique_together = [("template", "user")]
        indexes = [models.Index(fields=["template", "-created_at"])]
        ordering = ["-created_at"]


class UserTemplateCollection(models.Model):
    """用户收藏。"""

    template = models.ForeignKey(
        UserTemplate, on_delete=models.CASCADE, related_name="collections",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="ugc_collections",
    )
    collection_name = models.CharField(
        max_length=64, blank=True, default="",
        help_text="收藏夹名（默认 '默认收藏夹'）",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_user_template_collection"
        unique_together = [("template", "user")]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["collection_name"]),
        ]
        ordering = ["-created_at"]
