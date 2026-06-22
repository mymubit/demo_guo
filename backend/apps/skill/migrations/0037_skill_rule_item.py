# -*- coding: utf-8 -*-
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0036_remove_agentskill_compat_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="SkillRuleItem",
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
                    "rule_key",
                    models.CharField(
                        db_index=True,
                        help_text="全站唯一稳定标识，如 t1.global.philosophy.core_formula",
                        max_length=256,
                        verbose_name="规则键",
                    ),
                ),
                (
                    "tier",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Tier1·全局铁律"),
                            (2, "Tier2·品类规范"),
                            (3, "Tier3·节点流程"),
                            (4, "Tier4·合规熔断"),
                        ],
                        db_index=True,
                        verbose_name="层级",
                    ),
                ),
                (
                    "scope_type",
                    models.CharField(
                        choices=[("global", "全局"), ("genre", "题材"), ("node", "节点")],
                        db_index=True,
                        default="global",
                        max_length=16,
                        verbose_name="范围类型",
                    ),
                ),
                (
                    "scope_key",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        default="",
                        max_length=128,
                        verbose_name="范围键",
                    ),
                ),
                (
                    "section",
                    models.CharField(db_index=True, max_length=64, verbose_name="规则分区"),
                ),
                (
                    "item_type",
                    models.CharField(
                        choices=[("meta", "元信息"), ("rule", "规则条目")],
                        db_index=True,
                        default="rule",
                        max_length=16,
                        verbose_name="条目类型",
                    ),
                ),
                ("title", models.CharField(max_length=512, verbose_name="标题")),
                (
                    "body",
                    models.TextField(help_text="渲染进 Prompt 的可读文本", verbose_name="规则正文"),
                ),
                (
                    "payload",
                    models.JSONField(blank=True, default=dict, verbose_name="结构化附加"),
                ),
                (
                    "priority",
                    models.IntegerField(db_index=True, default=100, verbose_name="优先级"),
                ),
                ("sort_order", models.IntegerField(default=0, verbose_name="排序")),
                (
                    "version_tag",
                    models.CharField(
                        db_index=True,
                        default="v5.0.0",
                        max_length=32,
                        verbose_name="版本标签",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "已生效"),
                            ("draft", "草稿（待审核）"),
                            ("archived", "已归档"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=16,
                        verbose_name="状态",
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("file_import", "JSON文件导入"),
                            ("admin", "后台手动录入"),
                            ("evolve_audit", "进化审计提案"),
                        ],
                        db_index=True,
                        default="admin",
                        max_length=16,
                        verbose_name="来源",
                    ),
                ),
                ("note", models.TextField(blank=True, default="", verbose_name="备注")),
                (
                    "apply_count",
                    models.PositiveBigIntegerField(default=0, verbose_name="引用次数"),
                ),
                (
                    "last_applied_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="最近引用时间"),
                ),
                (
                    "approved_by",
                    models.CharField(blank=True, default="", max_length=128, verbose_name="审核人"),
                ),
                (
                    "approved_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="审核时间"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "config",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="items",
                        to="skill.skillruleconfig",
                        verbose_name="来源配置包",
                    ),
                ),
            ],
            options={
                "verbose_name": "技能规则条目",
                "verbose_name_plural": "技能规则条目",
                "db_table": "skill_rule_item",
                "ordering": [
                    "tier",
                    "scope_type",
                    "scope_key",
                    "section",
                    "sort_order",
                    "priority",
                    "-created_at",
                ],
            },
        ),
        migrations.AddIndex(
            model_name="skillruleitem",
            index=models.Index(
                fields=["tier", "scope_type", "scope_key", "section", "status"],
                name="skill_rule_item_main_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="skillruleitem",
            index=models.Index(fields=["status", "-apply_count"], name="skill_rule_item_apply_idx"),
        ),
        migrations.AddConstraint(
            model_name="skillruleitem",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "active")),
                fields=("rule_key",),
                name="skill_rule_item_active_key_uniq",
            ),
        ),
    ]
