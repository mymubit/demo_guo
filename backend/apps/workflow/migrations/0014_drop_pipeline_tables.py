# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0013_remove_legacy_tables"),
        ("creation", "0028_remove_legacy_pipeline_fields"),
    ]

    operations = [
        migrations.DeleteModel(name="FusionPipelineNode"),
        migrations.DeleteModel(name="FusionJsonSchema"),
        migrations.DeleteModel(name="FusionPipelinePack"),
        migrations.DeleteModel(name="WorkflowTemplate"),
    ]
