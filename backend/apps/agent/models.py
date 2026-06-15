# -*- coding: utf-8 -*-
"""Agent 中心数据模型 — db_table 与 skill app 迁态前一致。"""
from __future__ import annotations

import uuid

from django.db import models


class AgentLlmRouteConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route_key = models.CharField("路由键", max_length=64, unique=True, db_index=True)
    display_name = models.CharField("展示名称", max_length=128, blank=True, default="")
    llm_provider = models.ForeignKey(
        "skill.LlmProvider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_llm_routes",
        verbose_name="指定大模型",
    )
    max_tokens = models.PositiveIntegerField("Max Tokens", null=True, blank=True)
    is_active = models.BooleanField("启用", default=True)
    sort_order = models.IntegerField("排序", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Agent LLM 路由"
        verbose_name_plural = verbose_name
        db_table = "skill_agent_llm_route"
        ordering = ["sort_order", "route_key"]

    def __str__(self) -> str:
        return f"{self.route_key} · {self.display_name or self.route_key}"


class AgentRegistryConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=64, unique=True, default="default")
    display_name = models.CharField("展示名称", max_length=128, blank=True, default="Agent 注册表")
    registry = models.JSONField("Agent Registry JSON", default=dict, blank=True)
    is_active = models.BooleanField("启用", default=False, db_index=True)
    note = models.CharField("备注", max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Agent 注册表配置"
        verbose_name_plural = verbose_name
        db_table = "skill_agent_registry_config"
        ordering = ["-is_active", "config_key"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            AgentRegistryConfig.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)

    def __str__(self) -> str:
        flag = " [active]" if self.is_active else ""
        return f"{self.display_name or self.config_key}{flag}"


class ReviewScoringConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=32, unique=True, default="default")
    weights = models.JSONField("维度权重", default=dict, blank=True)
    grade_thresholds = models.JSONField("等级阈值", default=dict, blank=True)
    pass_threshold = models.PositiveSmallIntegerField("通过分数线", default=70)
    min_sub_item_score = models.PositiveSmallIntegerField("子项最低分", default=75)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "质量审查评分"
        verbose_name_plural = verbose_name
        db_table = "skill_review_scoring_config"

    def __str__(self) -> str:
        return f"审查评分 · 通过线 {self.pass_threshold}"
