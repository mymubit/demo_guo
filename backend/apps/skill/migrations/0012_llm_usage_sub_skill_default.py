# -*- coding: utf-8 -*-
# Generated manually: ensure sub_skill_id has DB default for legacy INSERT paths

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0011_llm_usage_execution_run"),
    ]

    operations = [
        migrations.AlterField(
            model_name="llmusagelog",
            name="sub_skill_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                max_length=128,
                verbose_name="子技能 ID",
            ),
        ),
        migrations.RunSQL(
            sql=(
                "UPDATE skill_llm_usage_log SET sub_skill_id = '' "
                "WHERE sub_skill_id IS NULL;"
                "ALTER TABLE skill_llm_usage_log "
                "ALTER COLUMN sub_skill_id SET DEFAULT '';"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
