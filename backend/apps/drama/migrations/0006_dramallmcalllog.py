# -*- coding: utf-8 -*-
"""LLM 调用日志表。"""
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("drama", "0005_dramallmprovider"),
    ]

    operations = [
        migrations.CreateModel(
            name="DramaLlmCallLog",
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
                ("actor", models.CharField(default="system", max_length=128, verbose_name="操作人")),
                ("role", models.CharField(blank=True, default="", max_length=64, verbose_name="技能角色")),
                (
                    "purpose",
                    models.CharField(
                        choices=[
                            ("artifact_generation", "角色产物生成"),
                            ("quality_scoring", "质量评分"),
                            ("compliance_check", "合规检查"),
                            ("connectivity_test", "连通性测试"),
                        ],
                        default="artifact_generation",
                        max_length=64,
                        verbose_name="调用用途",
                    ),
                ),
                ("seq_in_job", models.PositiveIntegerField(default=0, verbose_name="任务内序号")),
                ("model_name", models.CharField(blank=True, default="", max_length=128, verbose_name="模型")),
                ("base_url", models.CharField(blank=True, default="", max_length=512, verbose_name="接口地址")),
                ("system_prompt", models.TextField(blank=True, default="", verbose_name="系统提示词")),
                ("user_prompt", models.TextField(blank=True, default="", verbose_name="用户提示词")),
                ("response_text", models.TextField(blank=True, default="", verbose_name="模型回复正文")),
                ("response_body", models.JSONField(blank=True, null=True, verbose_name="原始响应")),
                (
                    "status",
                    models.CharField(
                        choices=[("success", "成功"), ("error", "失败")],
                        default="success",
                        max_length=16,
                        verbose_name="状态",
                    ),
                ),
                ("http_status", models.PositiveIntegerField(blank=True, null=True, verbose_name="HTTP 状态码")),
                ("error_message", models.TextField(blank=True, default="", verbose_name="错误信息")),
                ("latency_ms", models.PositiveIntegerField(default=0, verbose_name="耗时(ms)")),
                ("prompt_tokens", models.PositiveIntegerField(blank=True, null=True, verbose_name="Prompt Tokens")),
                (
                    "completion_tokens",
                    models.PositiveIntegerField(blank=True, null=True, verbose_name="Completion Tokens"),
                ),
                ("total_tokens", models.PositiveIntegerField(blank=True, null=True, verbose_name="Total Tokens")),
                (
                    "provider_request_id",
                    models.CharField(blank=True, default="", max_length=128, verbose_name="厂商 Request ID"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "generation_job",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="llm_call_logs",
                        to="drama.dramagenerationjob",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="llm_call_logs",
                        to="drama.dramaproject",
                    ),
                ),
            ],
            options={
                "verbose_name": "LLM 调用日志",
                "verbose_name_plural": "LLM 调用日志",
                "db_table": "drama_llm_call_log",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["project", "-created_at"], name="drama_llm_p_created_idx"),
                    models.Index(
                        fields=["generation_job", "seq_in_job"],
                        name="drama_llm_job_seq_idx",
                    ),
                    models.Index(fields=["role", "-created_at"], name="drama_llm_role_created_idx"),
                    models.Index(fields=["status", "-created_at"], name="drama_llm_status_created_idx"),
                ],
            },
        ),
    ]
