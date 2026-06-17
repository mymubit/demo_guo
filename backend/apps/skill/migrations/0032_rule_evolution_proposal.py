# -*- coding: utf-8 -*-
"""规则进化提案表（原 skill/evolution 子目录迁移并入 skill app）。"""

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0031_creation_skill_catalog"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RuleEvolutionProposal",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="提案ID",
                    ),
                ),
                (
                    "trigger_project_id",
                    models.UUIDField(
                        blank=True,
                        null=True,
                        verbose_name="触发项目",
                    ),
                ),
                (
                    "trigger_reason",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=200,
                        verbose_name="触发原因",
                    ),
                ),
                (
                    "target_skill_id",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=100,
                        verbose_name="目标技能",
                    ),
                ),
                (
                    "target_tier",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=20,
                        verbose_name="目标规则层",
                    ),
                ),
                (
                    "target_scope_key",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=100,
                        verbose_name="目标范围",
                    ),
                ),
                (
                    "current_value",
                    models.JSONField(blank=True, default=dict, verbose_name="当前值"),
                ),
                (
                    "proposed_value",
                    models.JSONField(blank=True, default=dict, verbose_name="提案值"),
                ),
                (
                    "change_reason",
                    models.TextField(blank=True, default="", verbose_name="修改理由"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "草稿"),
                            ("pending_approval", "待审批"),
                            ("approved", "已审批"),
                            ("rejected", "已拒绝"),
                            ("applied", "已应用"),
                        ],
                        default="draft",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                (
                    "proposed_by",
                    models.CharField(
                        choices=[("ai", "AI自动生成"), ("manual", "人工创建")],
                        default="ai",
                        max_length=50,
                        verbose_name="提案来源",
                    ),
                ),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_evolution_proposals",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="审批人",
                    ),
                ),
                (
                    "approved_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="审批时间"),
                ),
                (
                    "approval_comment",
                    models.TextField(blank=True, default="", verbose_name="审批意见"),
                ),
                (
                    "applied_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="应用时间"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "规则修改提案",
                "verbose_name_plural": "规则修改提案",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="ruleevolutionproposal",
            index=models.Index(
                fields=["status", "-created_at"],
                name="skill_proposal_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="ruleevolutionproposal",
            index=models.Index(
                fields=["trigger_project_id"],
                name="skill_proposal_trigger_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="ruleevolutionproposal",
            index=models.Index(
                fields=["target_skill_id", "target_tier"],
                name="skill_proposal_target_idx",
            ),
        ),
    ]
