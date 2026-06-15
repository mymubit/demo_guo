# Generated manually for catalog pricing + usage cost

import uuid

import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0009_llm_usage_log"),
    ]

    operations = [
        migrations.AddField(
            model_name="llmmodelcatalog",
            name="input_price_per_million",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=10,
                null=True,
                verbose_name="输入单价(元/百万Token)",
            ),
        ),
        migrations.AddField(
            model_name="llmmodelcatalog",
            name="output_price_per_million",
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                max_digits=10,
                null=True,
                verbose_name="输出单价(元/百万Token)",
            ),
        ),
        migrations.AddField(
            model_name="llmusagelog",
            name="estimated_cost_yuan",
            field=models.DecimalField(
                decimal_places=6,
                default=Decimal("0"),
                max_digits=12,
                verbose_name="估算费用(元)",
            ),
        ),
    ]
