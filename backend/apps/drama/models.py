# -*- coding: utf-8 -*-
"""Drama Skills 专属数据模型。"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class DramaProject(models.Model):
    """Short Drama Project 扩展信息。"""

    class TrackMode(models.TextChoices):
        FAST = "fast", "快速通道（8角色）"
        EXPERT = "expert", "专家通道（36角色）"

    class Stage(models.TextChoices):
        STRATEGY = "strategy", "战略选题"
        WORLDBUILDING = "worldbuilding", "世界构建"
        PLOT_DESIGN = "plot_design", "剧情设计"
        WRITING = "writing", "剧本创作"
        REVIEW = "review", "评审质控"
        POLISH = "polish", "修改润色"
        PRODUCTION = "production", "制作宣发"
        COMPLIANCE = "compliance", "合规审查"
        DELIVERED = "delivered", "已交付"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 关联到已有的 Project（软关联，避免跨app强依赖）
    project_id = models.UUIDField("关联项目ID", db_index=True, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="drama_projects",
        verbose_name="创作者",
    )

    # 项目基础信息
    title = models.CharField("剧名", max_length=128)
    genre_code = models.CharField("题材代码", max_length=32, default="family-revenge")
    total_episodes = models.IntegerField("总集数", default=30)
    target_platform = models.CharField(
        "目标平台", max_length=32, default="douyin",
        choices=[("douyin", "抖音"), ("kuaishou", "快手"), ("weixin", "微信小程序"), ("all", "通用")],
    )
    track_mode = models.CharField("创作模式", max_length=16, choices=TrackMode.choices, default=TrackMode.FAST)
    current_stage = models.CharField("当前阶段", max_length=32, choices=Stage.choices, default=Stage.STRATEGY)

    # 进度追踪：已完成的角色列表
    completed_roles = models.JSONField("已完成角色", default=list)

    # 质量数据
    word_count_stats = models.JSONField(
        "字数统计", default=dict,
        help_text="每集字数统计：{'ep1': {'total': 1050, 'dialogue': 320, 'scenes': 2}, ...}",
    )
    quality_scores = models.JSONField(
        "8维评分", default=dict,
        help_text="{'overall': 82, 'format': 88, 'structure': 85, ...}",
    )
    delivery_status = models.CharField(
        "交付状态", max_length=16, default="pending",
        choices=[("pending", "待交付"), ("ready", "可交付"), ("delivered", "已交付")],
    )

    # Token 消耗统计（冗余存储，加速查询）
    total_tokens_used = models.IntegerField("累计Token消耗", default=0)
    total_cost_cents = models.IntegerField("累计费用（分）", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_project"
        verbose_name = "Drama Project"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title}（{self.total_episodes}集/{self.get_track_mode_display()}）"

    def get_completion_rate(self) -> float:
        """获取完成率（基于track_mode）。"""
        from apps.drama.defaults import DRAMA_FAST_TRACK_ROLES, DRAMA_ROLE_DEFAULTS

        if self.track_mode == self.TrackMode.FAST:
            total = len(DRAMA_FAST_TRACK_ROLES)
        else:
            total = len(DRAMA_ROLE_DEFAULTS)

        completed = len(self.completed_roles or [])
        return round(completed / total * 100, 1) if total > 0 else 0.0


class DramaRoleExecution(models.Model):
    """单次角色执行记录。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待执行"
        RUNNING = "running", "执行中"
        SUCCESS = "success", "成功"
        FAILED = "failed", "失败"
        SKIPPED = "skipped", "跳过"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drama_project = models.ForeignKey(
        DramaProject, on_delete=models.CASCADE,
        related_name="role_executions", verbose_name="剧本项目",
    )
    agent_id = models.CharField("角色ID", max_length=64, db_index=True)
    agent_name_zh = models.CharField("角色中文名", max_length=64)

    status = models.CharField("状态", max_length=16, choices=Status.choices, default=Status.PENDING)

    # 输入输出
    input_artifacts = models.JSONField("输入产物", default=dict)
    output_artifacts = models.JSONField("输出产物", default=dict)

    # 执行统计
    prompt_tokens = models.IntegerField("提示词Token", default=0)
    completion_tokens = models.IntegerField("生成Token", default=0)
    total_tokens = models.IntegerField("总Token", default=0)
    cost_cents = models.IntegerField("费用（分）", default=0)
    elapsed_seconds = models.FloatField("耗时（秒）", null=True, blank=True)

    # 错误信息
    error_message = models.TextField("错误信息", blank=True, default="")

    # 使用的模型信息
    llm_provider = models.CharField("LLM Provider", max_length=64, blank=True, default="")
    llm_model = models.CharField("LLM Model", max_length=128, blank=True, default="")

    started_at = models.DateTimeField("开始时间", null=True, blank=True)
    finished_at = models.DateTimeField("完成时间", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_role_execution"
        verbose_name = "角色执行记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["drama_project", "agent_id"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.drama_project.title} / {self.agent_name_zh} ({self.get_status_display()})"
