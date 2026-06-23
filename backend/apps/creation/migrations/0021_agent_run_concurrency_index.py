# -*- coding: utf-8 -*-
# Generated manually for agent run concurrency guard

from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0020_remove_legacy_tables"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="agentexecutionrun",
            index=models.Index(fields=["project", "status"], name="creation_ag_project_status_idx"),
        ),
        migrations.AddConstraint(
            model_name="agentexecutionrun",
            constraint=models.UniqueConstraint(
                condition=Q(status="running"),
                fields=("project",),
                name="uniq_running_agent_per_project",
            ),
        ),
    ]
