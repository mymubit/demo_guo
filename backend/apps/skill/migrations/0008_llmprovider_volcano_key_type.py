# -*- coding: utf-8 -*-
# Generated manually for volcano_key_type on LlmProvider

from django.db import migrations, models


def backfill_volcano_key_type(apps, schema_editor):
    LlmProvider = apps.get_model("skill", "LlmProvider")
    for row in LlmProvider.objects.all().iterator():
        base_url = (row.base_url or "").rstrip("/")
        if not base_url:
            continue
        if "volces.com" not in base_url.lower() and "volcengine" not in base_url.lower():
            continue
        if "/api/coding" in base_url:
            row.volcano_key_type = "coding_plan"
        else:
            row.volcano_key_type = "payg"
        row.save(update_fields=["volcano_key_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0007_agent_llm_route_config"),
    ]

    operations = [
        migrations.AddField(
            model_name="llmprovider",
            name="volcano_key_type",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="payg=按量付费 /api/v3；coding_plan=Coding Plan /api/coding/v3",
                max_length=32,
                verbose_name="火山 Key 类型",
            ),
        ),
        migrations.RunPython(backfill_volcano_key_type, migrations.RunPython.noop),
    ]
