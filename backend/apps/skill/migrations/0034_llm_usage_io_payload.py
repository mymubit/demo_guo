# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0032_rule_evolution_proposal"),
    ]

    operations = [
        migrations.AddField(
            model_name="llmusagelog",
            name="request_payload",
            field=models.JSONField(blank=True, default=dict, verbose_name="请求体(调试)"),
        ),
        migrations.AddField(
            model_name="llmusagelog",
            name="response_payload",
            field=models.JSONField(blank=True, default=dict, verbose_name="响应体(调试)"),
        ),
    ]
