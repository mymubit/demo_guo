# -*- coding: utf-8 -*-
"""Drama Skills 专属数据模型。"""
from __future__ import annotations

import uuid
from typing import Any, Dict

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


class DramaEpisodeArtifact(models.Model):
    """
    每集的产物存储（支持多版本，用于修改建议应用）。

    设计原则：
    - 每集每个artifact_key保存一条记录（upsert语义）
    - version字段记录当前是第几版（初版=1，每次apply建议后+1）
    - diff_from_base 存储相对于上一版的变更（供前端diff视图展示）
    """

    class ArtifactKey(models.TextChoices):
        EPISODE_SCRIPT = "episode_script", "单集剧本"
        REVIEW_REPORT = "review_report", "审稿报告"
        QUALITY_REPORT = "quality_report", "质量报告"
        DIALOGUE_NOTES = "dialogue_notes", "对白优化建议"
        POLISH_RESULT = "polish_result", "润色结果"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drama_project = models.ForeignKey(
        DramaProject, on_delete=models.CASCADE,
        related_name="episode_artifacts", verbose_name="剧本项目",
    )
    episode_number = models.PositiveSmallIntegerField("集号", db_index=True)
    artifact_key = models.CharField("产物类型", max_length=32, choices=ArtifactKey.choices)
    version = models.PositiveSmallIntegerField("版本号", default=1)
    content = models.JSONField("产物内容", default=dict)
    # 相对前一版本的变更描述（纯文本 diff 摘要，供前端展示）
    diff_summary = models.TextField("变更摘要", blank=True, default="")
    # 生成此版本的角色
    produced_by_agent = models.CharField("生成角色", max_length=64, blank=True, default="")
    # 质量分（此版本的质量评估结果，避免重复查询）
    quality_score = models.FloatField("质量分", null=True, blank=True)
    # 字数
    word_count = models.IntegerField("字数", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_episode_artifact"
        verbose_name = "分集产物"
        verbose_name_plural = verbose_name
        # 每集每种产物只保留最新版，多版本用version区分
        unique_together = [("drama_project", "episode_number", "artifact_key", "version")]
        ordering = ["episode_number", "artifact_key", "-version"]
        indexes = [
            models.Index(fields=["drama_project", "episode_number"]),
            models.Index(fields=["drama_project", "artifact_key"]),
        ]

    def __str__(self) -> str:
        return f"{self.drama_project.title} E{self.episode_number:02d} {self.artifact_key} v{self.version}"


class DramaEpisodeQuality(models.Model):
    """每集的质量评估详情（分集评估，而非整剧整体）。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drama_project = models.ForeignKey(
        DramaProject, on_delete=models.CASCADE,
        related_name="episode_qualities", verbose_name="剧本项目",
    )
    episode_number = models.PositiveSmallIntegerField("集号", db_index=True)
    # 8维度评分
    scores = models.JSONField("8维评分", default=dict,
        help_text='{"format":85,"structure":80,"character":75,...,"overall":82}')
    # 扣分项详情（关键新增）
    issues = models.JSONField("问题清单", default=list,
        help_text='[{"dimension":"格式规范","severity":"error","desc":"台词使用了引号","suggestion":"改用冒号后接内容"}]')
    # 字数达标情况
    word_count_result = models.JSONField("字数验证", default=dict)
    # 综合建议
    summary = models.TextField("综合评估意见", blank=True, default="")
    evaluated_by_agent = models.CharField("评估角色", max_length=64, default="drama.quality-reporter")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_episode_quality"
        verbose_name = "分集质量评估"
        verbose_name_plural = verbose_name
        unique_together = [("drama_project", "episode_number")]
        ordering = ["episode_number"]

    def get_overall_score(self) -> float:
        return self.scores.get("overall", 0.0)

    def get_grade(self) -> str:
        s = self.get_overall_score()
        return "S" if s >= 90 else "A" if s >= 80 else "B" if s >= 75 else "C" if s >= 60 else "D"

    def __str__(self) -> str:
        return f"{self.drama_project.title} E{self.episode_number:02d} 质量评估 {self.get_overall_score()}分"


class DramaEpisodePlan(models.Model):
    """
    分集生成计划 — 解决100集token爆炸和质量控制问题。

    设计原则：
    1. 分批执行：每批5-10集，每批完成后立即质检（质量gate）
    2. 质量gate：低于阈值（默认75分）自动触发重写任务
    3. 断点续写：记录每集的生成状态，中断后可从最后成功处续写
    4. 成本估算：提前计算token消耗，避免超出预算
    """

    class EpisodeStatus(models.TextChoices):
        PENDING = "pending", "待生成"
        QUEUED = "queued", "排队中"
        GENERATING = "generating", "生成中"
        REVIEWING = "reviewing", "质检中"
        PASS = "pass", "质检通过"
        FAIL = "fail", "质检不通过"
        REWRITE = "rewrite", "重写中"
        DONE = "done", "已完成"
        SKIPPED = "skipped", "已跳过"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drama_project = models.ForeignKey(
        DramaProject, on_delete=models.CASCADE,
        related_name="episode_plans", verbose_name="剧本项目",
    )
    episode_number = models.PositiveSmallIntegerField("集号", db_index=True)
    status = models.CharField("状态", max_length=16, choices=EpisodeStatus.choices, default=EpisodeStatus.PENDING)

    # 质量控制
    quality_score = models.FloatField("质量分", null=True, blank=True)
    quality_gate_threshold = models.FloatField("质量门槛", default=75.0)
    quality_gate_passed = models.BooleanField("质量门槛通过", default=False)

    # 重写控制（防止无限循环重写）
    rewrite_count = models.PositiveSmallIntegerField("重写次数", default=0)
    max_rewrites = models.PositiveSmallIntegerField("最大重写次数", default=2)

    # 批次信息（第几批次）
    batch_number = models.PositiveSmallIntegerField("批次号", default=1,
        help_text="每批5-10集，按批次编排")

    # Token估算（生成前预估，生成后更新为实际值）
    estimated_tokens = models.IntegerField("预估Token", default=0)
    actual_tokens = models.IntegerField("实际Token", default=0)

    # 执行时间记录
    started_at = models.DateTimeField("开始时间", null=True, blank=True)
    finished_at = models.DateTimeField("完成时间", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_episode_plan"
        verbose_name = "分集生成计划"
        verbose_name_plural = verbose_name
        unique_together = [("drama_project", "episode_number")]
        ordering = ["episode_number"]
        indexes = [
            models.Index(fields=["drama_project", "status"]),
            models.Index(fields=["drama_project", "batch_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.drama_project.title} E{self.episode_number:02d} [{self.get_status_display()}]"

    def needs_rewrite(self) -> bool:
        """判断是否需要重写（质检不通过且未超过重写次数限制）。"""
        return (
            self.status == self.EpisodeStatus.FAIL
            and self.rewrite_count < self.max_rewrites
        )

    def can_proceed_to_next(self) -> bool:
        """判断是否可以继续生成下一集。"""
        return self.status in [self.EpisodeStatus.PASS, self.EpisodeStatus.DONE, self.EpisodeStatus.SKIPPED]


class DramaGenerationPlan(models.Model):
    """
    全局生成计划 — 管理整部剧的分批生成策略。

    100集剧本的典型生成流程：
    1. 生成大纲（plot-architect）- 1次全局调用
    2. 按批次生成剧本（每批5集）- 20批次
    3. 每批生成后：质检 → 通过则继续 → 不通过则重写
    4. 全部完成后：整剧合规检查（compliance-guard）
    """

    class PlanStatus(models.TextChoices):
        DRAFT = "draft", "草稿"
        ACTIVE = "active", "进行中"
        PAUSED = "paused", "已暂停"
        COMPLETED = "completed", "已完成"
        ABANDONED = "abandoned", "已放弃"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drama_project = models.OneToOneField(
        DramaProject, on_delete=models.CASCADE,
        related_name="generation_plan", verbose_name="剧本项目",
    )
    status = models.CharField("计划状态", max_length=16, choices=PlanStatus.choices, default=PlanStatus.DRAFT)

    # 分批配置
    batch_size = models.PositiveSmallIntegerField("每批集数", default=5,
        help_text="建议5-10集/批，平衡质量和效率")
    total_batches = models.PositiveSmallIntegerField("总批次", default=0)
    completed_batches = models.PositiveSmallIntegerField("已完成批次", default=0)
    current_batch = models.PositiveSmallIntegerField("当前批次", default=1)

    # 质量控制配置
    quality_gate_enabled = models.BooleanField("启用质量门槛", default=True)
    quality_gate_score = models.FloatField("质量门槛分数", default=75.0,
        help_text="低于此分数触发重写，建议70-80")
    auto_proceed_on_pass = models.BooleanField("通过后自动继续", default=False,
        help_text="True=自动生成下一批，False=每批需手动确认")

    # 成本控制
    token_budget = models.IntegerField("Token预算", default=0,
        help_text="0=不限制，非0=超出后暂停")
    tokens_used = models.IntegerField("已用Token", default=0)

    # 中断恢复
    last_completed_episode = models.PositiveSmallIntegerField("最后完成集号", default=0,
        help_text="断点续写用：从此集后继续")

    # 时间估算
    avg_tokens_per_episode = models.IntegerField("每集平均Token", default=0)
    estimated_total_minutes = models.FloatField("预估总耗时（分钟）", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_generation_plan"
        verbose_name = "全局生成计划"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"{self.drama_project.title} 生成计划 [{self.get_status_display()}]"

    def get_progress_pct(self) -> float:
        total = self.drama_project.total_episodes
        return round(self.last_completed_episode / total * 100, 1) if total > 0 else 0

    def get_remaining_episodes(self) -> int:
        return max(0, self.drama_project.total_episodes - self.last_completed_episode)

    def estimate_remaining_cost(self) -> Dict:
        """估算剩余生成成本（Token + 时间）。"""
        remaining = self.get_remaining_episodes()
        avg = self.avg_tokens_per_episode or 12000  # 默认每集约12000 tokens
        est_tokens = remaining * avg
        # 假设平均处理速度 800 tokens/秒（实际因模型而异）
        est_minutes = est_tokens / 800 / 60
        return {
            "remaining_episodes": remaining,
            "estimated_tokens": est_tokens,
            "estimated_minutes": round(est_minutes, 1),
            "estimated_hours": round(est_minutes / 60, 1),
        }


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
