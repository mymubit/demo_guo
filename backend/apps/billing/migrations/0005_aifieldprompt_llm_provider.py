# Generated manually — per-field AI LLM provider override

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0004_aifieldpromptconfig"),
        ("skill", "0002_llmprovider"),
    ]

    operations = [
        migrations.AddField(
            model_name="aifieldpromptconfig",
            name="llm_provider",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ai_field_prompts",
                to="skill.llmprovider",
                verbose_name="指定大模型",
            ),
        ),
    ]
