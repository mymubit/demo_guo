# -*- coding: utf-8 -*-
from django.db import migrations, models


def backfill_cost_split(apps, schema_editor):
    from apps.skill.llm.pricing import estimate_cost_breakdown, resolve_pricing

    LlmUsageLog = apps.get_model("skill", "LlmUsageLog")
    for log in LlmUsageLog.objects.all().iterator(chunk_size=500):
        inp_price, out_price = resolve_pricing(
            provider_id=log.provider_id,
            model_name=log.model_name,
        )
        inp_cost, out_cost, total = estimate_cost_breakdown(
            prompt_tokens=log.prompt_tokens,
            completion_tokens=log.completion_tokens,
            input_price_per_million=inp_price,
            output_price_per_million=out_price,
        )
        LlmUsageLog.objects.filter(pk=log.pk).update(
            estimated_input_cost_yuan=inp_cost,
            estimated_output_cost_yuan=out_cost,
            estimated_cost_yuan=total,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("skill", "0012_llm_usage_sub_skill_default"),
    ]

    operations = [
        migrations.AddField(
            model_name="llmusagelog",
            name="estimated_input_cost_yuan",
            field=models.DecimalField(
                decimal_places=6,
                default=0,
                max_digits=12,
                verbose_name="估算输入费用(元)",
            ),
        ),
        migrations.AddField(
            model_name="llmusagelog",
            name="estimated_output_cost_yuan",
            field=models.DecimalField(
                decimal_places=6,
                default=0,
                max_digits=12,
                verbose_name="估算输出费用(元)",
            ),
        ),
        migrations.RunPython(backfill_cost_split, migrations.RunPython.noop),
    ]
