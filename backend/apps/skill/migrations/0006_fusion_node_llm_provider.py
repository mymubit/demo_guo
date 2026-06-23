# -*- coding: utf-8 -*-
# Generated manually — per-node LLM provider override

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0005_operational_configs"),
    ]

    operations = [
        migrations.AddField(
            model_name="fusionnodellmpromptconfig",
            name="llm_provider",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="fusion_node_prompts",
                to="skill.llmprovider",
                verbose_name="指定大模型",
            ),
        ),
    ]
