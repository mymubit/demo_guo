# -*- coding: utf-8 -*-
"""短剧领域模型。"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class DramaProject(models.Model):
    """短剧项目主表。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="drama_projects",
    )
    title = models.CharField("标题", max_length=200)
    settings = models.JSONField("项目设置", default=dict)
    settings_revision = models.PositiveIntegerField("设置版本", default=1)
    skills_version = models.CharField("技能版本", max_length=32, default="5.0.0")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_project"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["owner", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return self.title


class DramaWorkflowState(models.Model):
    """流程状态持久化，version 用于乐观锁。"""

    project = models.OneToOneField(
        DramaProject,
        on_delete=models.CASCADE,
        related_name="workflow_state",
        primary_key=True,
    )
    state = models.JSONField("状态快照", default=dict)
    version = models.PositiveIntegerField("状态版本", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_workflow_state"


class DramaArtifactVersion(models.Model):
    """产物版本表。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        DramaProject,
        on_delete=models.CASCADE,
        related_name="artifact_versions",
    )
    artifact_key = models.CharField("产物键", max_length=64, db_index=True)
    version = models.PositiveIntegerField("版本号", default=1)
    schema_version = models.CharField("Schema 版本", max_length=64)
    payload = models.JSONField("内容")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_artifact_version"
        ordering = ["artifact_key", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "artifact_key", "version"],
                name="uniq_artifact_version",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "artifact_key", "-version"]),
        ]

    def __str__(self) -> str:
        return f"{self.project_id}:{self.artifact_key}@v{self.version}"


class DramaCommand(models.Model):
    """工作流命令幂等记录。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待处理"
        COMPLETED = "completed", "已完成"
        FAILED = "failed", "失败"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        DramaProject,
        on_delete=models.CASCADE,
        related_name="commands",
    )
    command_id = models.CharField("命令 ID", max_length=128)
    event = models.CharField("事件", max_length=64)
    payload = models.JSONField("请求体", default=dict)
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    response_snapshot = models.JSONField("响应快照", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_command"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "command_id"],
                name="uniq_project_command",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "command_id"]),
        ]


class DramaGenerationJob(models.Model):
    """异步生成任务。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待执行"
        QUEUED = "queued", "已入队"
        RUNNING = "running", "执行中"
        COMPLETED = "completed", "已完成"
        FAILED = "failed", "失败"
        DISABLED = "disabled", "已禁用"

    class JobType(models.TextChoices):
        GENERATION = "generation", "生成"
        SCORING = "scoring", "评分"
        COMPLIANCE = "compliance", "合规"
        EXTERNAL_REVIEW = "external_review", "外部审稿"
        PARALLEL_JUDGE = "parallel_judge", "并行评审"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generation_jobs",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        DramaProject,
        on_delete=models.CASCADE,
        related_name="generation_jobs",
        null=True,
        blank=True,
    )
    job_type = models.CharField("任务类型", max_length=32, choices=JobType.choices)
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    request_payload = models.JSONField("请求", default=dict)
    result_payload = models.JSONField("结果", null=True, blank=True)
    progress_events = models.JSONField("进度事件", default=list)
    error_message = models.TextField("错误信息", blank=True, default="")
    celery_task_id = models.CharField("Celery 任务 ID", max_length=64, blank=True, default="")
    command_id = models.CharField("命令 ID", max_length=128, blank=True, default="")
    role = models.CharField("角色", max_length=64, blank=True, default="")
    artifact_key = models.CharField("产物键", max_length=64, blank=True, default="")
    workflow_version = models.PositiveIntegerField("工作流版本", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_generation_job"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["celery_task_id"]),
            models.Index(fields=["project", "command_id"]),
            models.Index(fields=["owner", "command_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "command_id"],
                condition=models.Q(command_id__gt=""),
                name="uniq_generation_project_command",
            ),
            models.UniqueConstraint(
                fields=["owner", "command_id"],
                condition=models.Q(project__isnull=True, command_id__gt=""),
                name="uniq_generation_owner_command",
            ),
        ]


class DramaConfigRevision(models.Model):
    """运营配置覆盖不可变历史。"""

    revision = models.PositiveIntegerField("版本号", unique=True)
    overlay = models.JSONField("覆盖内容")
    updated_by = models.CharField("操作人", max_length=128)
    change_reason = models.CharField("变更原因", max_length=500)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_config_revision"
        ordering = ["revision"]


class DramaAuditEvent(models.Model):
    """持久化审计事件。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        DramaProject,
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    actor = models.CharField("操作人", max_length=128)
    action = models.CharField("动作", max_length=64)
    detail = models.JSONField("详情", default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_audit_event"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]
