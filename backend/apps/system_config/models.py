# -*- coding: utf-8 -*-
"""动态配置中心模型。"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class SystemConfigCategory(models.Model):
    """配置分类。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField("分类编码", max_length=64, unique=True, db_index=True)
    name = models.CharField("分类名称", max_length=80)
    description = models.TextField("分类说明", blank=True, default="")
    sort_order = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("启用", default=True, db_index=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "system_config_category"
        verbose_name = "配置分类"
        verbose_name_plural = verbose_name
        ordering = ["sort_order", "code"]
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} · {self.name}"


class SystemConfigItem(models.Model):
    """通用配置项。"""

    class ValueType(models.TextChoices):
        STRING = "string", "字符串"
        INT = "int", "整数"
        FLOAT = "float", "浮点数"
        BOOL = "bool", "布尔"
        JSON = "json", "JSON对象"
        ARRAY = "array", "JSON数组"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        SystemConfigCategory,
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name="配置分类",
    )
    config_key = models.CharField("配置键", max_length=160, unique=True, db_index=True)
    config_name = models.CharField("配置名称", max_length=120)
    value_type = models.CharField("值类型", max_length=16, choices=ValueType.choices)
    value = models.JSONField("配置值", default=None, null=True, blank=True)
    default_value = models.JSONField("默认值", default=None, null=True, blank=True)
    description = models.TextField("备注", blank=True, default="")
    validation_schema = models.JSONField("校验规则", default=dict, blank=True)
    is_active = models.BooleanField("启用", default=True, db_index=True)
    is_sensitive = models.BooleanField("敏感配置", default=False, db_index=True)
    is_public = models.BooleanField("公开读取", default=False, db_index=True)
    requires_restart = models.BooleanField("需要重启", default=False)
    version = models.PositiveIntegerField("版本号", default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_system_configs",
        verbose_name="创建人",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_system_configs",
        verbose_name="更新人",
    )
    created_at = models.DateTimeField("创建时间", default=timezone.now)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    deleted_at = models.DateTimeField("删除时间", null=True, blank=True, db_index=True)

    class Meta:
        db_table = "system_config_item"
        verbose_name = "配置项"
        verbose_name_plural = verbose_name
        ordering = ["category__sort_order", "config_key"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["is_public", "is_active"]),
            models.Index(fields=["updated_at"]),
            models.Index(fields=["deleted_at", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.config_key

    @property
    def effective_value(self):
        return self.value if self.value is not None else self.default_value

    def soft_delete(self, user=None) -> None:
        self.deleted_at = timezone.now()
        self.is_active = False
        if user and getattr(user, "is_authenticated", False):
            self.updated_by = user
        self.save(update_fields=["deleted_at", "is_active", "updated_by", "updated_at"])


class SensitiveWord(models.Model):
    """敏感词表（append-only）。

    仅支持新增，不提供修改/删除入口；如需下线由人工 SQL 软删。
    用于在 C 端创作链路中（项目名/角色名/正文）做内容拦截。
    """

    SEVERITY_HIGH = "high"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_LOW = "low"

    SEVERITY_CHOICES = [
        (SEVERITY_HIGH, "高"),
        (SEVERITY_MEDIUM, "中"),
        (SEVERITY_LOW, "低"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    word = models.CharField("敏感词", max_length=128, db_index=True)
    category = models.CharField("分类", max_length=64, blank=True, default="")
    severity = models.CharField(
        "严重程度",
        max_length=16,
        choices=SEVERITY_CHOICES,
        default=SEVERITY_MEDIUM,
        db_index=True,
    )
    note = models.CharField("备注", max_length=255, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_sensitive_words",
        verbose_name="创建人",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)

    class Meta:
        db_table = "system_config_sensitive_word"
        verbose_name = "敏感词"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["word", "severity"]),
            models.Index(fields=["severity", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"[{self.get_severity_display()}] {self.word}"


class SystemConfigAuditLog(models.Model):
    """配置变更审计日志。"""

    class Action(models.TextChoices):
        CREATE = "create", "新增"
        UPDATE = "update", "更新"
        TOGGLE = "toggle", "启用禁用"
        DELETE = "delete", "删除"
        REFRESH_CACHE = "refresh_cache", "刷新缓存"
        RESTORE_DEFAULT = "restore_default", "恢复默认"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(
        SystemConfigItem,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        verbose_name="配置项",
    )
    config_key = models.CharField("配置键", max_length=160, db_index=True)
    action = models.CharField("操作", max_length=32, choices=Action.choices, db_index=True)
    old_value = models.JSONField("旧值", null=True, blank=True)
    new_value = models.JSONField("新值", null=True, blank=True)
    change_reason = models.CharField("变更原因", max_length=300, blank=True, default="")
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="system_config_audit_logs",
        verbose_name="操作人",
    )
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("User-Agent", max_length=512, blank=True, default="")
    created_at = models.DateTimeField("创建时间", default=timezone.now, db_index=True)

    class Meta:
        db_table = "system_config_audit_log"
        verbose_name = "配置变更日志"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["config_key", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.config_key} · {self.action}"
