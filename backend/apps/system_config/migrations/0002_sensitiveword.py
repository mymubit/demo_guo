# Generated for SensitiveWord append-only table
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("system_config", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SensitiveWord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("word", models.CharField(db_index=True, max_length=128, verbose_name="敏感词")),
                ("category", models.CharField(blank=True, default="", max_length=64, verbose_name="分类")),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("high", "高"),
                            ("medium", "中"),
                            ("low", "低"),
                        ],
                        db_index=True,
                        default="medium",
                        max_length=16,
                        verbose_name="严重程度",
                    ),
                ),
                ("note", models.CharField(blank=True, default="", max_length=255, verbose_name="备注")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="created_sensitive_words",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="创建人",
                    ),
                ),
            ],
            options={
                "verbose_name": "敏感词",
                "verbose_name_plural": "敏感词",
                "db_table": "system_config_sensitive_word",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="sensitiveword",
            index=models.Index(fields=["word", "severity"], name="scw_word_sev_idx"),
        ),
        migrations.AddIndex(
            model_name="sensitiveword",
            index=models.Index(fields=["severity", "-created_at"], name="scw_sev_time_idx"),
        ),
    ]
