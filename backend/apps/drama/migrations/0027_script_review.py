# Generated manually for standalone script review

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("drama", "0026_cache_hit_pricing"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScriptReview",
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
                ("title", models.CharField(max_length=200)),
                ("source_type", models.CharField(max_length=16)),
                (
                    "source_filename",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("script_text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="script_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="script_reviews",
                        to="drama.v3project",
                    ),
                ),
            ],
            options={
                "db_table": "drama_script_review",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="ScriptReviewRun",
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
                ("kind", models.CharField(max_length=16)),
                ("status", models.CharField(default="queued", max_length=32)),
                ("report_payload", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "command_run",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="script_review_runs",
                        to="drama.v3commandrun",
                    ),
                ),
                (
                    "review",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="runs",
                        to="drama.scriptreview",
                    ),
                ),
            ],
            options={
                "db_table": "drama_script_review_run",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="scriptreview",
            index=models.Index(
                fields=["owner", "-updated_at"],
                name="drama_scrip_owner_i_7a2c1d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="scriptreviewrun",
            index=models.Index(
                fields=["review", "kind", "-created_at"],
                name="drama_scrip_review__9f4e2a_idx",
            ),
        ),
    ]
