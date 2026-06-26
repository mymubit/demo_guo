# -*- coding: utf-8 -*-
"""Drama Skills 专属数据模型（项目主表已合并至 creation.Project）。"""
from __future__ import annotations

import uuid
from typing import Dict

from django.db import models

from apps.creation.models import Project


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
        EPISODE_OUTLINE = "episode_outline", "单集大纲"
        EPISODE_NARRATIVE = "episode_narrative", "单集叙事方案"
        REVIEW_REPORT = "review_report", "审稿报告"
        QUALITY_REPORT = "quality_report", "质量报告"
        DIALOGUE_NOTES = "dialogue_notes", "对白优化建议"
        POLISH_RESULT = "polish_result", "润色结果"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="drama_episode_artifacts",
        verbose_name="剧本项目",
    )
    episode_number = models.PositiveSmallIntegerField("集号", db_index=True)
    artifact_key = models.CharField("产物类型", max_length=32, choices=ArtifactKey.choices)
    version = models.PositiveSmallIntegerField("版本号", default=1)
    content = models.JSONField("产物内容", default=dict)
    diff_summary = models.TextField("变更摘要", blank=True, default="")
    produced_by_agent = models.CharField("生成角色", max_length=64, blank=True, default="")
    quality_score = models.FloatField("质量分", null=True, blank=True)
    word_count = models.IntegerField("字数", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_episode_artifact"
        verbose_name = "分集产物"
        verbose_name_plural = verbose_name
        unique_together = [("project", "episode_number", "artifact_key", "version")]
        ordering = ["episode_number", "artifact_key", "-version"]
        indexes = [
            models.Index(fields=["project", "episode_number"]),
            models.Index(fields=["project", "artifact_key"]),
        ]

    def __str__(self) -> str:
        title = self.project.title or self.project.theme
        return f"{title} E{self.episode_number:02d} {self.artifact_key} v{self.version}"


class DramaEpisodeQuality(models.Model):
    """每集的质量评估详情（分集评估，而非整剧整体）。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="drama_episode_qualities",
        verbose_name="剧本项目",
    )
    episode_number = models.PositiveSmallIntegerField("集号", db_index=True)
    scores = models.JSONField(
        "8维评分",
        default=dict,
        help_text='{"format":85,"structure":80,"character":75,...,"overall":82}',
    )
    issues = models.JSONField(
        "问题清单",
        default=list,
        help_text='[{"dimension":"格式规范","severity":"error","desc":"台词使用了引号","suggestion":"改用冒号后接内容"}]',
    )
    word_count_result = models.JSONField("字数验证", default=dict)
    summary = models.TextField("综合评估意见", blank=True, default="")
    evaluated_by_agent = models.CharField("评估角色", max_length=64, default="drama.quality-reporter")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_episode_quality"
        verbose_name = "分集质量评估"
        verbose_name_plural = verbose_name
        unique_together = [("project", "episode_number")]
        ordering = ["episode_number"]

    def get_overall_score(self) -> float:
        return self.scores.get("overall", 0.0)

    def get_grade(self) -> str:
        score = self.get_overall_score()
        return "S" if score >= 90 else "A" if score >= 80 else "B" if score >= 75 else "C" if score >= 60 else "D"

    def __str__(self) -> str:
        title = self.project.title or self.project.theme
        return f"{title} E{self.episode_number:02d} 质量评估 {self.get_overall_score()}分"


class DramaEpisodePlan(models.Model):
    """分集生成计划 — 解决大批量集数 token 爆炸和质量控制问题。"""

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
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="drama_episode_plans",
        verbose_name="剧本项目",
    )
    episode_number = models.PositiveSmallIntegerField("集号", db_index=True)
    status = models.CharField("状态", max_length=16, choices=EpisodeStatus.choices, default=EpisodeStatus.PENDING)
    quality_score = models.FloatField("质量分", null=True, blank=True)
    quality_gate_threshold = models.FloatField("质量门槛", default=75.0)
    quality_gate_passed = models.BooleanField("质量门槛通过", default=False)
    rewrite_count = models.PositiveSmallIntegerField("重写次数", default=0)
    max_rewrites = models.PositiveSmallIntegerField("最大重写次数", default=2)
    batch_number = models.PositiveSmallIntegerField("批次号", default=1, help_text="每批5-10集，按批次编排")
    estimated_tokens = models.IntegerField("预估Token", default=0)
    actual_tokens = models.IntegerField("实际Token", default=0)
    started_at = models.DateTimeField("开始时间", null=True, blank=True)
    finished_at = models.DateTimeField("完成时间", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_episode_plan"
        verbose_name = "分集生成计划"
        verbose_name_plural = verbose_name
        unique_together = [("project", "episode_number")]
        ordering = ["episode_number"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "batch_number"]),
        ]

    def __str__(self) -> str:
        title = self.project.title or self.project.theme
        return f"{title} E{self.episode_number:02d} [{self.get_status_display()}]"

    def needs_rewrite(self) -> bool:
        return (
            self.status == self.EpisodeStatus.FAIL
            and self.rewrite_count < self.max_rewrites
        )

    def can_proceed_to_next(self) -> bool:
        return self.status in [
            self.EpisodeStatus.PASS,
            self.EpisodeStatus.DONE,
            self.EpisodeStatus.SKIPPED,
        ]


class DramaGenerationPlan(models.Model):
    """全局生成计划 — 管理整部剧的分批生成策略。"""

    class PlanStatus(models.TextChoices):
        DRAFT = "draft", "草稿"
        ACTIVE = "active", "进行中"
        PAUSED = "paused", "已暂停"
        COMPLETED = "completed", "已完成"
        ABANDONED = "abandoned", "已放弃"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="drama_generation_plan",
        verbose_name="剧本项目",
    )
    status = models.CharField("计划状态", max_length=16, choices=PlanStatus.choices, default=PlanStatus.DRAFT)
    batch_size = models.PositiveSmallIntegerField("每批集数", default=5, help_text="建议5-10集/批，平衡质量和效率")
    total_batches = models.PositiveSmallIntegerField("总批次", default=0)
    completed_batches = models.PositiveSmallIntegerField("已完成批次", default=0)
    current_batch = models.PositiveSmallIntegerField("当前批次", default=1)
    quality_gate_enabled = models.BooleanField("启用质量门槛", default=True)
    quality_gate_score = models.FloatField("质量门槛分数", default=75.0, help_text="低于此分数触发重写，建议70-80")
    auto_proceed_on_pass = models.BooleanField("通过后自动继续", default=False, help_text="True=自动生成下一批，False=每批需手动确认")
    token_budget = models.IntegerField("Token预算", default=0, help_text="0=不限制，非0=超出后暂停")
    tokens_used = models.IntegerField("已用Token", default=0)
    last_completed_episode = models.PositiveSmallIntegerField("最后完成集号", default=0, help_text="断点续写用：从此集后继续")
    avg_tokens_per_episode = models.IntegerField("每集平均Token", default=0)
    estimated_total_minutes = models.FloatField("预估总耗时（分钟）", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_generation_plan"
        verbose_name = "全局生成计划"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        title = self.project.title or self.project.theme
        return f"{title} 生成计划 [{self.get_status_display()}]"

    def get_progress_pct(self) -> float:
        total = self.project.episode_count
        return round(self.last_completed_episode / total * 100, 1) if total > 0 else 0

    def get_remaining_episodes(self) -> int:
        return max(0, self.project.episode_count - self.last_completed_episode)

    def estimate_remaining_cost(self) -> Dict:
        remaining = self.get_remaining_episodes()
        avg = self.avg_tokens_per_episode or 12000
        est_tokens = remaining * avg
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
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="drama_role_executions",
        verbose_name="剧本项目",
    )
    agent_id = models.CharField("角色ID", max_length=64, db_index=True)
    agent_name_zh = models.CharField("角色中文名", max_length=64)
    status = models.CharField("状态", max_length=16, choices=Status.choices, default=Status.PENDING)
    input_artifacts = models.JSONField("输入产物", default=dict)
    output_artifacts = models.JSONField("输出产物", default=dict)
    prompt_tokens = models.IntegerField("提示词Token", default=0)
    completion_tokens = models.IntegerField("生成Token", default=0)
    total_tokens = models.IntegerField("总Token", default=0)
    cost_cents = models.IntegerField("费用（分）", default=0)
    elapsed_seconds = models.FloatField("耗时（秒）", null=True, blank=True)
    error_message = models.TextField("错误信息", blank=True, default="")
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
            models.Index(fields=["project", "agent_id"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        title = self.project.title or self.project.theme
        return f"{title} / {self.agent_name_zh} ({self.get_status_display()})"
