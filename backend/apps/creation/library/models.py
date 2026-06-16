# -*- coding: utf-8 -*-
"""
素材库模型 — 参考作品结构化存储。

支持：
- 上传小说/剧本 PDF/Word
- 自动解析提取世界观/人设/剧情结构
- 创作时自动注入参考内容到上下文
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class ReferenceMaterial(models.Model):
    """参考素材

    存储用户上传的小说/剧本文件，解析后提取结构化内容供创作时注入。
    """

    # 素材类型
    TYPE_NOVEL = "novel"
    TYPE_SCREENPLAY = "screenplay"
    TYPE_OTHER = "other"

    TYPE_CHOICES = [
        (TYPE_NOVEL, "小说"),
        (TYPE_SCREENPLAY, "剧本"),
        (TYPE_OTHER, "其他"),
    ]

    # 解析状态
    STATUS_PARSING = "parsing"
    STATUS_READY = "ready"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PARSING, "解析中"),
        (STATUS_READY, "就绪"),
        (STATUS_FAILED, "解析失败"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="素材ID",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reference_materials",
        verbose_name="所属用户",
    )
    name = models.CharField("素材名称", max_length=200)
    material_type = models.CharField(
        "类型",
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_OTHER,
    )

    # 文件存储
    file_path = models.CharField("文件路径", max_length=500, blank=True, default="")
    file_size = models.IntegerField("文件大小(字节)", default=0)

    # 解析后的结构化内容
    parsed_content = models.JSONField(
        "解析内容",
        default=dict,
        blank=True,
        help_text=(
            "解析后的结构化内容，结构："
            '{"world":{"setting":"...","rules":["...",...]},'
            '"characters":[{"name":"...","role":"...","description":"..."}],'
            '"plot_structure":{"acts":[...],"twists":[...]},'
            '"themes":["...",...]}'
        ),
    )

    # 状态
    parse_status = models.CharField(
        "解析状态",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PARSING,
    )
    parse_error = models.TextField("解析错误", blank=True, default="")

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "参考素材"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["parse_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_material_type_display()})"


class ReferenceMaterialInjection(models.Model):
    """创作时注入记录 — 追踪哪个项目用了哪个素材"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="注入记录ID",
    )
    project = models.ForeignKey(
        "creation.Project",
        on_delete=models.CASCADE,
        related_name="material_injections",
        verbose_name="项目",
    )
    material = models.ForeignKey(
        ReferenceMaterial,
        on_delete=models.CASCADE,
        related_name="injections",
        verbose_name="素材",
    )
    injected_fields = models.JSONField(
        "注入字段",
        default=list,
        blank=True,
        help_text="已注入的字段列表，如 ['world', 'characters']",
    )
    injected_at = models.DateTimeField("注入时间", auto_now_add=True)

    class Meta:
        verbose_name = "素材注入记录"
        verbose_name_plural = verbose_name
        ordering = ["-injected_at"]
        indexes = [
            models.Index(fields=["project", "-injected_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.project_id} → {self.material_id}"
