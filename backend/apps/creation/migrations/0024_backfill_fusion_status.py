# -*- coding: utf-8 -*-
"""存量项目 fusion_status 为空时，从 legacy status 回填。"""
from django.db import migrations

MAPPING = {
    "pending": "draft",
    "running": "writing",
    "awaiting": "reviewing",
    "completed": "ready",
    "failed": "blocked",
}


def backfill_fusion_status(apps, schema_editor):
    Project = apps.get_model("creation", "Project")
    for project in Project.objects.all().only("id", "status", "fusion_status"):
        if (project.fusion_status or "").strip():
            continue
        fusion = MAPPING.get(project.status)
        if fusion:
            Project.objects.filter(pk=project.pk).update(fusion_status=fusion)


def reverse_backfill(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0023_project_novel_text"),
    ]

    operations = [
        migrations.RunPython(backfill_fusion_status, reverse_backfill),
    ]
