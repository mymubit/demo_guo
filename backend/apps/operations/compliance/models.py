"""合规规则模型。

业务闭环：
  ① 运营在后台维护敏感词 / 题材黑名单 / 规则
  ② 创作管线在产出前 / 产出后调用 compliance 检查
  ③ 命中规则自动记入 violation_log
  ④ 规则可热更新：增删改后立即生效
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.operations.constants import ComplianceCategory, ComplianceLevel


class SensitiveWord(models.Model):
    """敏感词。"""

    word = models.CharField(max_length=128, unique=True)
    category = models.CharField(max_length=32, choices=ComplianceCategory.choices)
    level = models.CharField(max_length=8, choices=ComplianceLevel.choices)
    description = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_sensitive_word"
        indexes = [
            models.Index(fields=["is_active", "category"]),
            models.Index(fields=["level", "is_active"]),
        ]
        ordering = ["-updated_at"]


class TopicBlacklist(models.Model):
    """题材黑名单。"""

    name = models.CharField(max_length=128, unique=True)
    keywords = models.JSONField(default=list, help_text="关键词列表")
    category = models.CharField(max_length=32, choices=ComplianceCategory.choices, default=ComplianceCategory.TOPIC_RISK)
    level = models.CharField(max_length=8, choices=ComplianceLevel.choices, default=ComplianceLevel.P0)
    reason = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_topic_blacklist"
        indexes = [models.Index(fields=["is_active", "category"])]
        ordering = ["-updated_at"]


class ComplianceRule(models.Model):
    """复合规则（基于敏感词 + 题材 + 自定义表达式）。"""

    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=32, choices=ComplianceCategory.choices)
    level = models.CharField(max_length=8, choices=ComplianceLevel.choices)
    # 规则表达（结构化）：{"require_words": [...], "exclude_words": [...], "scope": "title/outline/script/all"}
    rule_expr = models.JSONField(default=dict)
    scope = models.CharField(max_length=32, default="all", help_text="title/outline/script/all")
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_compliance_rule"
        indexes = [
            models.Index(fields=["is_active", "level"]),
            models.Index(fields=["category", "is_active"]),
        ]
        ordering = ["-updated_at"]


class ViolationLog(models.Model):
    """违规记录。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        related_name="violation_logs", null=True, blank=True,
    )
    project = models.ForeignKey(
        "creation.Project", on_delete=models.SET_NULL,
        related_name="violation_logs", null=True, blank=True,
    )
    category = models.CharField(max_length=32, choices=ComplianceCategory.choices)
    level = models.CharField(max_length=8, choices=ComplianceLevel.choices)
    source = models.CharField(max_length=32, default="auto", help_text="auto / manual / user_report")
    matched_text = models.TextField(blank=True, default="", help_text="命中文本片段")
    rule_name = models.CharField(max_length=128, blank=True, default="")
    action_taken = models.CharField(max_length=64, blank=True, default="", help_text="block / warn / record")
    handled = models.BooleanField(default=False)
    handled_by = models.CharField(max_length=64, blank=True, default="")
    handled_at = models.DateTimeField(null=True, blank=True)
    handle_note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_violation_log"
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["level", "-created_at"]),
            models.Index(fields=["handled", "-created_at"]),
        ]
        ordering = ["-created_at"]


class ComplianceRuleVersion(models.Model):
    """规则版本（每次发布快照）。"""

    version = models.CharField(max_length=32, unique=True)
    snapshot = models.JSONField(default=dict, help_text="规则库完整快照")
    note = models.TextField(blank=True, default="")
    published_by = models.CharField(max_length=64, blank=True, default="")
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ops_compliance_version"
        ordering = ["-published_at"]
