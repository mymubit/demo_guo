# Generated migration for generation job metadata fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drama", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="dramagenerationjob",
            name="artifact_key",
            field=models.CharField(blank=True, default="", max_length=64, verbose_name="产物键"),
        ),
        migrations.AddField(
            model_name="dramagenerationjob",
            name="command_id",
            field=models.CharField(blank=True, default="", max_length=128, verbose_name="命令 ID"),
        ),
        migrations.AddField(
            model_name="dramagenerationjob",
            name="role",
            field=models.CharField(blank=True, default="", max_length=64, verbose_name="角色"),
        ),
        migrations.AddField(
            model_name="dramagenerationjob",
            name="workflow_version",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="工作流版本"),
        ),
        migrations.AddIndex(
            model_name="dramagenerationjob",
            index=models.Index(fields=["project", "command_id"], name="drama_gener_project_8a4f21_idx"),
        ),
        migrations.AddConstraint(
            model_name="dramagenerationjob",
            constraint=models.UniqueConstraint(
                condition=models.Q(("command_id__gt", "")),
                fields=("project", "command_id"),
                name="uniq_generation_project_command",
            ),
        ),
    ]
