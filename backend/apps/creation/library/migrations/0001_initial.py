# -*- coding: utf-8 -*-
"""素材库初始迁移 — 创建 ReferenceMaterial 和 ReferenceMaterialInjection 表。"""

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0015_project_gray_flow_version"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ReferenceMaterial",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="素材ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=200, verbose_name="素材名称"),
                ),
                (
                    "material_type",
                    models.CharField(
                        choices=[("novel", "小说"), ("screenplay", "剧本"), ("other", "其他")],
                        default="other",
                        max_length=20,
                        verbose_name="类型",
                    ),
                ),
                (
                    "file_path",
                    models.CharField(blank=True, default="", max_length=500, verbose_name="文件路径"),
                ),
                (
                    "file_size",
                    models.IntegerField(default=0, verbose_name="文件大小(字节)"),
                ),
                (
                    "parsed_content",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "解析后的结构化内容，结构："
                            '{"world":{"setting":"...","rules":["...",...]},'
                            '"characters":[{"name":"...","role":"...","description":"..."}],'
                            '"plot_structure":{"acts":[...],"twists":[...]},'
                            '"themes":["...",...]}'
                        ),
                        verbose_name="解析内容",
                    ),
                ),
                (
                    "parse_status",
                    models.CharField(
                        choices=[("parsing", "解析中"), ("ready", "就绪"), ("failed", "解析失败")],
                        default="parsing",
                        max_length=20,
                        verbose_name="解析状态",
                    ),
                ),
                (
                    "parse_error",
                    models.TextField(blank=True, default="", verbose_name="解析错误"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reference_materials",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="所属用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "参考素材",
                "verbose_name_plural": "参考素材",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ReferenceMaterialInjection",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="注入记录ID",
                    ),
                ),
                (
                    "injected_fields",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="已注入的字段列表，如 ['world', 'characters']",
                        verbose_name="注入字段",
                    ),
                ),
                ("injected_at", models.DateTimeField(auto_now_add=True, verbose_name="注入时间")),
                (
                    "material",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="injections",
                        to="creation.referencematerial",
                        verbose_name="素材",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="material_injections",
                        to="creation.project",
                        verbose_name="项目",
                    ),
                ),
            ],
            options={
                "verbose_name": "素材注入记录",
                "verbose_name_plural": "素材注入记录",
                "ordering": ["-injected_at"],
            },
        ),
        migrations.AddIndex(
            model_name="referencematerial",
            index=models.Index(fields=["user", "-created_at"], name="creation_ref_user_d8e9c4_idx"),
        ),
        migrations.AddIndex(
            model_name="referencematerial",
            index=models.Index(fields=["parse_status"], name="creation_ref_parse_b7e8c2_idx"),
        ),
        migrations.AddIndex(
            model_name="referencematerialinjection",
            index=models.Index(fields=["project", "-injected_at"], name="creation_inj_projects_f5d8e3_idx"),
        ),
    ]
