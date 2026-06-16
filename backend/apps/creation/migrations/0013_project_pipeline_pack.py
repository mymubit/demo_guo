# -*- coding: utf-8 -*-
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0002_pipeline_template_fields"),
        ("creation", "0012_add_last_failed_dimensions"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="pipeline_pack",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="workflow.fusionpipelinepack",
                verbose_name="流水线模板",
            ),
        ),
    ]
