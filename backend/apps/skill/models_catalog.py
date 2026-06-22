# -*- coding: utf-8 -*-
"""Catalog 原子化与 AgentSkillSection（skill-agent/12、13）。"""
from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class AgentSkillSection(models.Model):
    """AgentSkillDefinition 分段 SSOT；content 为 sync 缓存。"""

    SECTION_SYSTEM = "system_prompt"
    SECTION_INPUT = "input_schema"
    SECTION_QUALITY = "quality_checklist"
    SECTION_ANTI = "anti_patterns"
    SECTION_EXAMPLES = "examples"
    SECTION_CHOICES = [
        (SECTION_SYSTEM, "System Prompt"),
        (SECTION_INPUT, "Input Schema"),
        (SECTION_QUALITY, "Quality Checklist"),
        (SECTION_ANTI, "Anti Patterns"),
        (SECTION_EXAMPLES, "Examples"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    skill = models.ForeignKey(
        "skill.AgentSkillDefinition",
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="技能",
    )
    section_key = models.CharField("分区键", max_length=64, choices=SECTION_CHOICES, db_index=True)
    section_content = models.TextField("分区内容", blank=True, default="")
    section_schema_json = models.JSONField("Schema JSON", default=dict, blank=True)
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True, db_index=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "skill_agent_skill_section"
        verbose_name = "Agent 技能分区"
        verbose_name_plural = verbose_name
        ordering = ["skill_id", "sort_order", "section_key"]
        unique_together = [["skill", "section_key"]]

    def __str__(self) -> str:
        return f"{self.skill_id} · {self.section_key}"


class ThemeActRatio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    theme = models.ForeignKey("skill.ThemeTemplate", on_delete=models.CASCADE, related_name="act_ratios")
    act_name = models.CharField("幕名称", max_length=64)
    ratio_percent = models.PositiveSmallIntegerField("占比%", default=0)
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        db_table = "skill_theme_act_ratio"
        verbose_name = "题材幕占比"
        verbose_name_plural = verbose_name
        ordering = ["sort_order"]


class ThemeEmotionCurve(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    theme = models.ForeignKey("skill.ThemeTemplate", on_delete=models.CASCADE, related_name="emotion_curves")
    episode_from = models.PositiveSmallIntegerField("起始集", default=1)
    episode_to = models.PositiveSmallIntegerField("结束集", default=1)
    emotion_value = models.SmallIntegerField("情绪值", default=0)
    label = models.CharField("标签", max_length=64, blank=True, default="")
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        db_table = "skill_theme_emotion_curve"
        verbose_name = "题材情绪曲线"
        verbose_name_plural = verbose_name
        ordering = ["sort_order"]


class ThemeHookType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    theme = models.ForeignKey("skill.ThemeTemplate", on_delete=models.CASCADE, related_name="hook_types")
    hook_type = models.CharField("钩子类型", max_length=64)
    description = models.CharField("说明", max_length=256, blank=True, default="")
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        db_table = "skill_theme_hook_type"
        verbose_name = "题材钩子类型"
        verbose_name_plural = verbose_name
        ordering = ["sort_order"]


class ThemeCharacterArchetype(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    theme = models.ForeignKey("skill.ThemeTemplate", on_delete=models.CASCADE, related_name="archetypes")
    name = models.CharField("原型名", max_length=128)
    description = models.TextField("描述", blank=True, default="")
    fit_genres = models.JSONField("适用题材", default=list, blank=True)
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        db_table = "skill_theme_character_archetype"
        verbose_name = "题材角色原型"
        verbose_name_plural = verbose_name
        ordering = ["sort_order"]


class ThemeEmotionalPeakMoment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    theme = models.ForeignKey("skill.ThemeTemplate", on_delete=models.CASCADE, related_name="peak_moments")
    episode_hint = models.CharField("集数提示", max_length=64, blank=True, default="")
    moment = models.TextField("峰值时刻")
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        db_table = "skill_theme_emotional_peak"
        verbose_name = "题材情绪峰值"
        verbose_name_plural = verbose_name
        ordering = ["sort_order"]


class ThemeReversalDensity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    theme = models.ForeignKey("skill.ThemeTemplate", on_delete=models.CASCADE, related_name="reversal_densities")
    stage = models.CharField("阶段", max_length=64)
    density = models.CharField("密度", max_length=32, blank=True, default="")
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True)

    class Meta:
        db_table = "skill_theme_reversal_density"
        verbose_name = "题材反转密度"
        verbose_name_plural = verbose_name
        ordering = ["sort_order"]
