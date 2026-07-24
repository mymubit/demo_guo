# Generated manually for project delete + usage rollup FK

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("drama", "0024_v3_llm_provider_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="v3usagedailyrollup",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="usage_daily_rollups",
                to="drama.v3project",
            ),
        ),
    ]
