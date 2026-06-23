# -*- coding: utf-8 -*-
# Generated manually — 参考库 DB SSOT + 审查子项最低分
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0024_delete_fusionnodellmpromptconfig"),
    ]

    operations = [
        migrations.AddField(
            model_name="reviewscoringconfig",
            name="min_sub_item_score",
            field=models.PositiveSmallIntegerField(default=75, verbose_name="子项最低分"),
        ),
        migrations.CreateModel(
            name="ReferenceLibraryConfig",
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
                    models.CharField(
                        default="default",
                        max_length=32,
                        unique=True,
                        verbose_name="配置键",
                    ),
                ),
                (
                    "content",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="键为文件名（如 industry-benchmarks.json），值为解析后的 JSON 对象",
                        verbose_name="参考库内容",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "参考库配置",
                "verbose_name_plural": "参考库配置",
                "db_table": "skill_reference_library_config",
            },
        ),
    ]
