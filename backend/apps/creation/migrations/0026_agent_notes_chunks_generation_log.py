# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0025_remove_project_status"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="agent_notes",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="跨 Agent 的用户偏好与拒绝项，如 rejects / style_preferences / character_guidance",
                verbose_name="Agent 项目记忆",
            ),
        ),
        migrations.CreateModel(
            name="ProjectChunk",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("kind", models.CharField(db_index=True, max_length=32, verbose_name="分片类型")),
                ("index", models.PositiveIntegerField(db_index=True, verbose_name="序号/集号")),
                ("data", models.JSONField(blank=True, default=dict, verbose_name="分片数据")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间")),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunks",
                        to="creation.project",
                        verbose_name="项目",
                    ),
                ),
                (
                    "run",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="chunks",
                        to="creation.agentexecutionrun",
                        verbose_name="执行记录",
                    ),
                ),
            ],
            options={
                "verbose_name": "项目分片",
                "verbose_name_plural": "项目分片",
                "db_table": "creation_project_chunk",
                "ordering": ["index"],
                "indexes": [
                    models.Index(
                        fields=["project", "kind", "index"],
                        name="creation_pc_proj_kind_idx",
                    ),
                ],
                "unique_together": {("project", "kind", "index")},
            },
        ),
        migrations.CreateModel(
            name="SkillGenerationLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("trace_id", models.CharField(db_index=True, max_length=64, verbose_name="追踪 ID")),
                (
                    "skill_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default="",
                        max_length=64,
                        verbose_name="技能 ID",
                    ),
                ),
                (
                    "agent_id",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default="",
                        max_length=64,
                        verbose_name="Agent ID",
                    ),
                ),
                ("prompt_tokens", models.PositiveIntegerField(blank=True, null=True, verbose_name="Prompt Tokens")),
                (
                    "completion_tokens",
                    models.PositiveIntegerField(blank=True, null=True, verbose_name="Completion Tokens"),
                ),
                ("total_tokens", models.PositiveIntegerField(blank=True, null=True, verbose_name="Total Tokens")),
                ("provider", models.CharField(blank=True, default="", max_length=128, verbose_name="Provider")),
                ("model", models.CharField(blank=True, default="", max_length=128, verbose_name="模型")),
                ("duration_ms", models.PositiveIntegerField(blank=True, null=True, verbose_name="耗时(ms)")),
                (
                    "status",
                    models.CharField(
                        choices=[("ok", "成功"), ("error", "失败"), ("truncated", "截断")],
                        db_index=True,
                        default="ok",
                        max_length=16,
                        verbose_name="状态",
                    ),
                ),
                ("error_message", models.TextField(blank=True, default="", verbose_name="错误信息")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间")),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="skill_generation_logs",
                        to="creation.project",
                        verbose_name="项目",
                    ),
                ),
                (
                    "run",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="generation_logs",
                        to="creation.agentexecutionrun",
                        verbose_name="执行记录",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="skill_generation_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "技能生成日志",
                "verbose_name_plural": "技能生成日志",
                "db_table": "creation_skill_generation_log",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["project", "-created_at"], name="creation_sgl_proj_idx"),
                    models.Index(fields=["trace_id"], name="creation_sgl_trace_idx"),
                ],
            },
        ),
    ]
