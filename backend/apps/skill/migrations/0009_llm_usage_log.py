# -*- coding: utf-8 -*-
# Generated manually for LlmUsageLog

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0003_project_workspace_mode"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("skill", "0008_llmprovider_volcano_key_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="LlmUsageLog",
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
                (
                    "provider_name",
                    models.CharField(
                        blank=True, default="", max_length=100, verbose_name="Provider 名称"
                    ),
                ),
                (
                    "model_name",
                    models.CharField(db_index=True, max_length=128, verbose_name="模型"),
                ),
                (
                    "prompt_tokens",
                    models.PositiveIntegerField(default=0, verbose_name="Prompt Tokens"),
                ),
                (
                    "completion_tokens",
                    models.PositiveIntegerField(default=0, verbose_name="Completion Tokens"),
                ),
                (
                    "total_tokens",
                    models.PositiveIntegerField(default=0, verbose_name="Total Tokens"),
                ),
                (
                    "source_type",
                    models.CharField(
                        choices=[
                            ("node", "融合节点"),
                            ("agent", "辅助 Agent"),
                            ("ai_field", "AI 字段"),
                            ("test", "连通测试"),
                            ("other", "其他"),
                        ],
                        db_index=True,
                        default="other",
                        max_length=32,
                        verbose_name="来源类型",
                    ),
                ),
                (
                    "source_key",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default="",
                        max_length=64,
                        verbose_name="来源标识",
                    ),
                ),
                ("success", models.BooleanField(default=True, verbose_name="成功")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间"),
                ),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="llm_usage_logs",
                        to="creation.project",
                        verbose_name="项目",
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="usage_logs",
                        to="skill.llmprovider",
                        verbose_name="Provider",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="llm_usage_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "大模型调用用量",
                "verbose_name_plural": "大模型调用用量",
                "db_table": "skill_llm_usage_log",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["-created_at", "model_name"],
                        name="skill_llm_u_created_8a1b0d_idx",
                    ),
                    models.Index(
                        fields=["-created_at", "provider_name"],
                        name="skill_llm_u_created_9b2c1e_idx",
                    ),
                ],
            },
        ),
    ]
