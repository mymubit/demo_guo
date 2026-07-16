# Generated manually for DramaLlmProvider

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("drama", "0004_artifact_schema_version_integer"),
    ]

    operations = [
        migrations.CreateModel(
            name="DramaLlmProvider",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100, verbose_name="展示名称")),
                ("base_url", models.CharField(blank=True, default="", max_length=512, verbose_name="Base URL")),
                ("model_name", models.CharField(default="gpt-4o-mini", max_length=128, verbose_name="模型名称")),
                ("api_key_encrypted", models.TextField(blank=True, default="", verbose_name="加密 API Key")),
                ("temperature", models.FloatField(default=0.7, verbose_name="Temperature")),
                ("max_tokens", models.PositiveIntegerField(default=4096, verbose_name="Max Tokens")),
                ("is_enabled", models.BooleanField(default=True, verbose_name="启用")),
                ("is_active", models.BooleanField(db_index=True, default=False, verbose_name="当前使用")),
                ("remark", models.CharField(blank=True, default="", max_length=255, verbose_name="备注")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "LLM 接入配置",
                "verbose_name_plural": "LLM 接入配置",
                "db_table": "drama_llm_provider",
                "ordering": ["-is_active", "-updated_at"],
            },
        ),
    ]
