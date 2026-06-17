# -*- coding: utf-8 -*-
"""
批量创作任务模型。

支持 CSV 上传批量创建创作项目，自动排队执行。
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class BatchJob(models.Model):
    """批量创作任务"""

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_PAUSED = "paused"

    STATUS_CHOICES = [
        (STATUS_PENDING, "待执行"),
        (STATUS_RUNNING, "执行中"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_FAILED, "失败"),
        (STATUS_PAUSED, "已暂停"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="任务ID",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="batch_jobs",
        verbose_name="所属用户",
    )
    name = models.CharField("任务名称", max_length=200)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    # 原始 CSV 数据（JSON 存储行列表）
    csv_data = models.JSONField("CSV 数据", default=list)

    # 统计
    total_count = models.IntegerField("总项目数", default=0)
    completed_count = models.IntegerField("已完成", default=0)
    failed_count = models.IntegerField("失败数", default=0)

    # 关联模板
    pipeline_pack_id = models.UUIDField("工作流包 ID", null=True, blank=True)
    theme = models.CharField("题材", max_length=64)

    created_at = models.DateTimeField("创建时间", default=timezone.now)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "批量创作任务"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"BatchJob[{self.status}] {self.name} ({self.id.hex[:8]})"


class BatchProject(models.Model):
    """批量任务中的单个创作子项目"""

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "待执行"),
        (STATUS_RUNNING, "执行中"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_FAILED, "失败"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="子项目ID",
    )
    batch_job = models.ForeignKey(
        BatchJob,
        on_delete=models.CASCADE,
        related_name="batch_projects",
        verbose_name="所属批量任务",
    )
    project = models.OneToOneField(
        "creation.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="batch_sub_project",
        verbose_name="创作项目",
    )

    row_index = models.IntegerField("CSV 行号")
    core_idea = models.TextField("核心创意")
    extra_params = models.JSONField("额外参数", default=dict)

    status = models.CharField(
        "状态",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    error_message = models.TextField("错误信息", blank=True, default="")

    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "批量创作子项目"
        verbose_name_plural = verbose_name
        ordering = ["row_index"]
        indexes = [
            models.Index(fields=["batch_job", "status"]),
            models.Index(fields=["row_index"]),
        ]

    def __str__(self) -> str:
        return f"BatchProject[{self.status}] row={self.row_index} ({self.id.hex[:8]})"
