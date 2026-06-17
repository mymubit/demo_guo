# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0017_batch_and_reference_material"),
    ]

    operations = [
        migrations.AddField(
            model_name="subskillexecutionlog",
            name="input_payload",
            field=models.JSONField(blank=True, default=dict, verbose_name="输入(完整)"),
        ),
        migrations.AddField(
            model_name="subskillexecutionlog",
            name="output_payload",
            field=models.JSONField(blank=True, default=dict, verbose_name="输出(完整)"),
        ),
        migrations.AddField(
            model_name="subskillexecutionlog",
            name="llm_io",
            field=models.JSONField(blank=True, default=dict, verbose_name="LLM 入出参"),
        ),
    ]
