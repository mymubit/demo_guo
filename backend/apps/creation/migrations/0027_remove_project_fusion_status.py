# -*- coding: utf-8 -*-
"""删除 legacy Project.fusion_status 列与相关索引。"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0026_agent_notes_chunks_generation_log"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="project",
            name="creation_pr_fusion_st_idx",
        ),
        migrations.RemoveIndex(
            model_name="project",
            name="creation_pr_abandon_fus_idx",
        ),
        migrations.RemoveIndex(
            model_name="project",
            name="creation_pr_created_fus_idx",
        ),
        migrations.RemoveField(
            model_name="project",
            name="fusion_status",
        ),
    ]
