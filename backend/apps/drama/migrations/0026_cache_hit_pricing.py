# Generated manually for cache hit pricing

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drama", "0025_v3_usage_rollup_project_cascade"),
    ]

    operations = [
        migrations.AddField(
            model_name="v3modelprice",
            name="price_cache_in_per_1k",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                help_text="缓存命中输入单价；空则按输入单价计",
                max_digits=16,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="dramallmcalllog",
            name="cached_prompt_tokens",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="缓存命中 Prompt Tokens",
            ),
        ),
        migrations.AddField(
            model_name="v3usagedailyrollup",
            name="cached_prompt_tokens",
            field=models.BigIntegerField(default=0),
        ),
    ]
