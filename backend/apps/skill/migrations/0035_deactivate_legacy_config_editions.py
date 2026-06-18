# -*- coding: utf-8 -*-
"""移除 legacy-demo / legacy-skills 配置条目（后台列表已过滤，此处清理存量）。"""
from django.db import migrations

LEGACY_EDITIONS = ("legacy-demo", "legacy-skills")


def remove_legacy_config_editions(apps, schema_editor):
    SkillConfigEntry = apps.get_model("skill", "SkillConfigEntry")
    SkillConfigEntry.objects.filter(edition__in=LEGACY_EDITIONS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0034_llm_usage_io_payload"),
    ]

    operations = [
        migrations.RunPython(remove_legacy_config_editions, migrations.RunPython.noop),
    ]
