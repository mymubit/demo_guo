# -*- coding: utf-8 -*-
"""
AI 规则进化 — 低评分项目分析 + 规则修改提案。

核心模型：
- RuleEvolutionProposal：规则修改提案，记录缺陷模式与建议的规则变更。
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class RuleEvolutionProposal(models.Model):
    """
    规则修改提案。

    当低评分项目（overall_score < 70）触发进化分析时，
    系统生成提案记录，包含当前值、提案值和修改理由。
    提案需人工审批后才可应用。
    """

    # 提案状态
    STATUS_DRAFT = "draft"
    STATUS_PENDING_APPROVAL = "pending_approval"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_APPLIED = "applied"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "草稿"),
        (STATUS_PENDING_APPROVAL, "待审批"),
        (STATUS_APPROVED, "已审批"),
        (STATUS_REJECTED, "已拒绝"),
        (STATUS_APPLIED, "已应用"),
    ]

    # 提案来源
    PROPOSED_BY_AI = "ai"
    PROPOSED_BY_MANUAL = "manual"

    PROPOSED_BY_CHOICES = [
        (PROPOSED_BY_AI, "AI自动生成"),
        (PROPOSED_BY_MANUAL, "人工创建"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="提案ID",
    )

    # 分析来源
    trigger_project_id = models.UUIDField(
        "触发项目",
        null=True,
        blank=True,
        help_text="触发本次提案的低评分项目 ID",
    )
    trigger_reason = models.CharField(
        "触发原因",
        max_length=200,
        blank=True,
        default="",
        help_text="如：连续3个项目在人物塑造维度低于70分",
    )

    # 提案内容 — 定位要修改的规则
    target_skill_id = models.CharField(
        "目标技能",
        max_length=100,
        blank=True,
        default="",
        help_text="如 drama-master-suite",
    )
    target_tier = models.CharField(
        "目标规则层",
        max_length=20,
        blank=True,
        default="",
        help_text="如 Tier2 / Tier3",
    )
    target_scope_key = models.CharField(
        "目标范围",
        max_length=100,
        blank=True,
        default="",
        help_text="题材代码（如 family-revenge）或节点 ID（如 node-5-script）",
    )

    # 规则值
    current_value = models.JSONField(
        "当前值",
        default=dict,
        blank=True,
        help_text="规则修改前的当前值",
    )
    proposed_value = models.JSONField(
        "提案值",
        default=dict,
        blank=True,
        help_text="建议修改为目标的值",
    )
    change_reason = models.TextField(
        "修改理由",
        blank=True,
        default="",
        help_text="AI 或人工提出的修改理由",
    )

    # 审批流
    status = models.CharField(
        "状态",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )
    proposed_by = models.CharField(
        "提案来源",
        max_length=50,
        default=PROPOSED_BY_AI,
        choices=PROPOSED_BY_CHOICES,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_evolution_proposals",
        verbose_name="审批人",
    )
    approved_at = models.DateTimeField(
        "审批时间",
        null=True,
        blank=True,
    )
    approval_comment = models.TextField(
        "审批意见",
        blank=True,
        default="",
    )
    applied_at = models.DateTimeField(
        "应用时间",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "规则修改提案"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["trigger_project_id"]),
            models.Index(fields=["target_skill_id", "target_tier"]),
        ]

    def __str__(self) -> str:
        return f"提案 {self.id} ({self.get_status_display()})"
