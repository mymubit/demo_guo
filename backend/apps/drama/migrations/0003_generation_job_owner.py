# Generated migration for generation job owner FK and orphan idempotency

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("drama", "0002_generation_job_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="dramagenerationjob",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="generation_jobs",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddIndex(
            model_name="dramagenerationjob",
            index=models.Index(
                fields=["owner", "command_id"],
                name="drama_gener_owner_c_91a2bd_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="dramagenerationjob",
            constraint=models.UniqueConstraint(
                condition=models.Q(("command_id__gt", ""), ("project__isnull", True)),
                fields=("owner", "command_id"),
                name="uniq_generation_owner_command",
            ),
        ),
    ]
