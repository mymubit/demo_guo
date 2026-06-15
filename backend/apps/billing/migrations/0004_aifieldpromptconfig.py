# Generated manually for AiFieldPromptConfig

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0003_actionpricing_member_only"),
    ]

    operations = [
        migrations.CreateModel(
            name="AiFieldPromptConfig",
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
                ("action_key", models.CharField(max_length=64, unique=True, verbose_name="动作键")),
                (
                    "display_name",
                    models.CharField(blank=True, default="", max_length=100, verbose_name="展示名称"),
                ),
                ("system_prompt", models.TextField(blank=True, default="", verbose_name="System 提示词")),
                (
                    "user_prompt_tpl",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="可用占位符：{theme} {episode_count} {core_idea} {audience} {reference_work}",
                        verbose_name="User 模板",
                    ),
                ),
                (
                    "system_prompt_fallback",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="JSON 模式失败时的文本降级提示词",
                        verbose_name="备用 System",
                    ),
                ),
                ("response_json", models.BooleanField(default=False, verbose_name="JSON 输出")),
                ("is_active", models.BooleanField(default=True, verbose_name="启用")),
                ("sort_order", models.IntegerField(default=0, verbose_name="排序")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "字段 AI 提示词",
                "verbose_name_plural": "字段 AI 提示词",
                "db_table": "billing_ai_field_prompt",
                "ordering": ["sort_order", "action_key"],
            },
        ),
    ]
