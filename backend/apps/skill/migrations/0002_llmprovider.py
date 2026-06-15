# Generated manually for LlmProvider

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LlmProvider",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100, verbose_name="展示名称")),
                (
                    "provider_type",
                    models.CharField(
                        choices=[("openai_compatible", "OpenAI 兼容")],
                        default="openai_compatible",
                        max_length=32,
                        verbose_name="接入类型",
                    ),
                ),
                ("api_key_encrypted", models.TextField(blank=True, default="", verbose_name="加密 API Key")),
                ("base_url", models.CharField(blank=True, default="", max_length=512, verbose_name="Base URL")),
                ("model_name", models.CharField(default="gpt-4o-mini", max_length=128, verbose_name="模型名称")),
                ("temperature", models.FloatField(default=0.7, verbose_name="Temperature")),
                ("max_tokens", models.PositiveIntegerField(default=4096, verbose_name="Max Tokens")),
                ("is_active", models.BooleanField(db_index=True, default=False, verbose_name="当前启用")),
                ("is_enabled", models.BooleanField(default=True, verbose_name="启用")),
                ("sort_order", models.IntegerField(default=0, verbose_name="排序")),
                ("remark", models.CharField(blank=True, default="", max_length=255, verbose_name="备注")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "大模型配置",
                "verbose_name_plural": "大模型配置",
                "db_table": "skill_llm_provider",
                "ordering": ["sort_order", "-created_at"],
            },
        ),
    ]
