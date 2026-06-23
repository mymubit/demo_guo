# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("creation", "0027_remove_project_fusion_status"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="pipeline_pack",
        ),
        migrations.RemoveField(
            model_name="project",
            name="current_node_index",
        ),
        migrations.RemoveField(
            model_name="project",
            name="total_nodes",
        ),
        migrations.RemoveField(
            model_name="project",
            name="gray_flow_version",
        ),
    ]
