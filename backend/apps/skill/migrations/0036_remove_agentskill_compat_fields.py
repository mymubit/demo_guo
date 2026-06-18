# -*- coding: utf-8 -*-
"""清理 AgentSkillDefinition 兼容字段 category / is_active。"""
from django.db import migrations


def migrate_inactive_to_deprecated(apps, schema_editor):
    AgentSkillDefinition = apps.get_model("skill", "AgentSkillDefinition")
    AgentSkillDefinition.objects.filter(is_active=False).exclude(
        lifecycle_status="deprecated",
    ).update(lifecycle_status="deprecated")


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0035_deactivate_legacy_config_editions"),
    ]

    operations = [
        migrations.RunPython(migrate_inactive_to_deprecated, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name="agentskilldefinition",
            options={
                "ordering": ["skill_layer", "skill_id"],
                "verbose_name": "Agent 技能定义",
                "verbose_name_plural": "Agent 技能定义",
            },
        ),
        migrations.RemoveField(
            model_name="agentskilldefinition",
            name="category",
        ),
        migrations.RemoveField(
            model_name="agentskilldefinition",
            name="is_active",
        ),
    ]
