# -*- coding: utf-8 -*-
"""CreationForm 原子子表（skill-agent/13 §3）。"""
from __future__ import annotations

import uuid

from django.db import models


class CreationPlatform(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=32, default="default", db_index=True)
    item_key = models.CharField("平台键", max_length=64, db_index=True)
    name = models.CharField("名称", max_length=128)
    description = models.TextField("说明", blank=True, default="")
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True, db_index=True)

    class Meta:
        db_table = "skill_creation_platform"
        verbose_name = "创作平台"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "item_key"]
        unique_together = [["config_key", "item_key"]]


class CreationBudgetLevel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=32, default="default", db_index=True)
    item_key = models.CharField("预算键", max_length=64, db_index=True)
    name = models.CharField("名称", max_length=128)
    description = models.TextField("说明", blank=True, default="")
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True, db_index=True)

    class Meta:
        db_table = "skill_creation_budget_level"
        verbose_name = "创作预算档位"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "item_key"]
        unique_together = [["config_key", "item_key"]]


class CreationEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=32, default="default", db_index=True)
    item_key = models.CharField("入口键", max_length=64, db_index=True)
    name = models.CharField("名称", max_length=128)
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True, db_index=True)

    class Meta:
        db_table = "skill_creation_entry"
        verbose_name = "创作入口"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "item_key"]
        unique_together = [["config_key", "item_key"]]


class CreationEntryProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=32, default="default", db_index=True)
    entry_key = models.CharField("入口键", max_length=64, db_index=True)
    profile = models.JSONField("Profile 配置", default=dict, blank=True)
    is_active = models.BooleanField("启用", default=True, db_index=True)

    class Meta:
        db_table = "skill_creation_entry_profile"
        verbose_name = "创作入口 Profile"
        verbose_name_plural = verbose_name
        unique_together = [["config_key", "entry_key"]]


class FormatVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=32, default="default", db_index=True)
    item_key = models.CharField("格式键", max_length=8, db_index=True)
    schema_key = models.CharField("Schema 键", max_length=32, blank=True, default="")
    name = models.CharField("名称", max_length=128)
    description = models.TextField("说明", blank=True, default="")
    scene_heading = models.CharField("场景标题样例", max_length=128, blank=True, default="")
    dialogue_marker = models.CharField("台词标记", max_length=64, blank=True, default="")
    action_marker = models.CharField("动作标记", max_length=64, blank=True, default="")
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True, db_index=True)

    class Meta:
        db_table = "skill_creation_format_variant"
        verbose_name = "剧本格式变体"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "item_key"]
        unique_together = [["config_key", "item_key"]]


class CreationThemeEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=32, default="default", db_index=True)
    theme_key = models.CharField("题材键", max_length=64, db_index=True)
    display_name = models.CharField("展示名", max_length=128, blank=True, default="")
    recommended_episodes = models.PositiveSmallIntegerField("推荐集数", null=True, blank=True)
    recommended_duration = models.PositiveSmallIntegerField("推荐时长(分)", null=True, blank=True)
    color = models.CharField("颜色", max_length=16, blank=True, default="#667eea")
    icon = models.CharField("图标", max_length=32, blank=True, default="🎬")
    is_enabled = models.BooleanField("启用", default=True, db_index=True)
    sort_order = models.IntegerField("排序", default=0)

    class Meta:
        db_table = "skill_creation_theme_entry"
        verbose_name = "创作题材入口"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "theme_key"]
        unique_together = [["config_key", "theme_key"]]


class EpisodeSettingsConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config_key = models.CharField("配置键", max_length=32, unique=True, default="default")
    min_episodes = models.PositiveSmallIntegerField("最少集数", default=20)
    max_episodes = models.PositiveSmallIntegerField("最多集数", default=200)
    step = models.PositiveSmallIntegerField("步进", default=10)
    default_episodes = models.PositiveSmallIntegerField("默认集数", default=80)
    presets = models.JSONField("快捷预设", default=list, blank=True)
    duration_minutes = models.PositiveSmallIntegerField("单集时长(分)", default=2)

    class Meta:
        db_table = "skill_episode_settings_config"
        verbose_name = "集数设置"
        verbose_name_plural = verbose_name
