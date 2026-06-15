# Generated manually for operational config models

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0004_fusion_pipeline_pack"),
    ]

    operations = [
        migrations.CreateModel(
            name="FusionNodeLlmPromptConfig",
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
                ("node_id", models.CharField(max_length=64, unique=True, verbose_name="节点 ID")),
                (
                    "display_name",
                    models.CharField(blank=True, default="", max_length=128, verbose_name="展示名称"),
                ),
                ("system_prompt", models.TextField(blank=True, default="", verbose_name="System 提示词")),
                (
                    "user_prompt_tpl",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="可用占位符：{upstream_json}",
                        verbose_name="User 模板",
                    ),
                ),
                ("constraints", models.TextField(blank=True, default="", verbose_name="附加约束")),
                ("is_active", models.BooleanField(default=True, verbose_name="启用")),
                ("sort_order", models.IntegerField(default=0, verbose_name="排序")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "融合节点 LLM 提示词",
                "verbose_name_plural": "融合节点 LLM 提示词",
                "db_table": "skill_fusion_node_llm_prompt",
                "ordering": ["sort_order", "node_id"],
            },
        ),
        migrations.CreateModel(
            name="CreationFormOverrideConfig",
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
                    "config_key",
                    models.CharField(default="default", max_length=32, unique=True, verbose_name="配置键"),
                ),
                ("overrides", models.JSONField(blank=True, default=dict, verbose_name="表单覆盖")),
                ("episode_settings", models.JSONField(blank=True, default=dict, verbose_name="集数默认值")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "创作表单覆盖",
                "verbose_name_plural": "创作表单覆盖",
                "db_table": "skill_creation_form_override",
            },
        ),
        migrations.CreateModel(
            name="ReviewScoringConfig",
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
                    "config_key",
                    models.CharField(default="default", max_length=32, unique=True, verbose_name="配置键"),
                ),
                ("weights", models.JSONField(blank=True, default=dict, verbose_name="维度权重")),
                ("grade_thresholds", models.JSONField(blank=True, default=dict, verbose_name="等级阈值")),
                ("pass_threshold", models.PositiveSmallIntegerField(default=70, verbose_name="通过分数线")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "质量审查评分",
                "verbose_name_plural": "质量审查评分",
                "db_table": "skill_review_scoring_config",
            },
        ),
    ]
