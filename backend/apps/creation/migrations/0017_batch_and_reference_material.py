# -*- coding: utf-8 -*-
"""批量创作与素材库表（原 batch/library 子目录迁移并入 creation app）。"""

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0016_project_content_quality_fields"),
        ("workflow", "__first__"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BatchJob",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="任务ID",
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="任务名称")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "待执行"),
                            ("running", "执行中"),
                            ("completed", "已完成"),
                            ("failed", "失败"),
                            ("paused", "已暂停"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                ("csv_data", models.JSONField(default=list, verbose_name="CSV 数据")),
                ("total_count", models.IntegerField(default=0, verbose_name="总项目数")),
                ("completed_count", models.IntegerField(default=0, verbose_name="已完成")),
                ("failed_count", models.IntegerField(default=0, verbose_name="失败数")),
                (
                    "pipeline_pack_id",
                    models.UUIDField(blank=True, null=True, verbose_name="工作流包 ID"),
                ),
                ("theme", models.CharField(max_length=64, verbose_name="题材")),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="创建时间",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="batch_jobs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="所属用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "批量创作任务",
                "verbose_name_plural": "批量创作任务",
                "ordering": ["-created_at"],
            },
        ),
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
                ("name", models.CharField(max_length=200, verbose_name="素材名称")),
                (
                    "material_type",
                    models.CharField(
                        choices=[
                            ("novel", "小说"),
                            ("screenplay", "剧本"),
                            ("other", "其他"),
                        ],
                        default="other",
                        max_length=20,
                        verbose_name="类型",
                    ),
                ),
                (
                    "file_path",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=500,
                        verbose_name="文件路径",
                    ),
                ),
                ("file_size", models.IntegerField(default=0, verbose_name="文件大小(字节)")),
                (
                    "parsed_content",
                    models.JSONField(blank=True, default=dict, verbose_name="解析内容"),
                ),
                (
                    "parse_status",
                    models.CharField(
                        choices=[
                            ("parsing", "解析中"),
                            ("ready", "就绪"),
                            ("failed", "解析失败"),
                        ],
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
            name="BatchProject",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="子项目ID",
                    ),
                ),
                ("row_index", models.IntegerField(verbose_name="CSV 行号")),
                ("core_idea", models.TextField(verbose_name="核心创意")),
                ("extra_params", models.JSONField(default=dict, verbose_name="额外参数")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "待执行"),
                            ("running", "执行中"),
                            ("completed", "已完成"),
                            ("failed", "失败"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                (
                    "error_message",
                    models.TextField(blank=True, default="", verbose_name="错误信息"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="创建时间",
                    ),
                ),
                (
                    "batch_job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="batch_projects",
                        to="creation.batchjob",
                        verbose_name="所属批量任务",
                    ),
                ),
                (
                    "project",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="batch_sub_project",
                        to="creation.project",
                        verbose_name="创作项目",
                    ),
                ),
            ],
            options={
                "verbose_name": "批量创作子项目",
                "verbose_name_plural": "批量创作子项目",
                "ordering": ["row_index"],
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
                    models.JSONField(blank=True, default=list, verbose_name="注入字段"),
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
            model_name="batchjob",
            index=models.Index(
                fields=["user", "-created_at"],
                name="creation_batch_user_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="batchjob",
            index=models.Index(fields=["status"], name="creation_batch_status_idx"),
        ),
        migrations.AddIndex(
            model_name="batchproject",
            index=models.Index(
                fields=["batch_job", "status"],
                name="creation_batchproj_job_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="batchproject",
            index=models.Index(fields=["row_index"], name="creation_batchproj_row_idx"),
        ),
        migrations.AddIndex(
            model_name="referencematerial",
            index=models.Index(
                fields=["user", "-created_at"],
                name="creation_refmat_user_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="referencematerial",
            index=models.Index(
                fields=["parse_status"],
                name="creation_refmat_parse_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="referencematerialinjection",
            index=models.Index(
                fields=["project", "-injected_at"],
                name="creation_refmat_inj_project_idx",
            ),
        ),
    ]
