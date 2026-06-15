# Generated manually for LLM usage linkage to agent execution runs

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0004_agent_execution_trace"),
        ("skill", "0010_llm_pricing_and_usage_cost"),
    ]

    operations = [
        migrations.AddField(
            model_name="llmusagelog",
            name="execution_run",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="llm_usage_logs",
                to="creation.agentexecutionrun",
                verbose_name="Agent 执行记录",
            ),
        ),
        migrations.AddField(
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
    ]
