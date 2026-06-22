# -*- coding: utf-8 -*-
from django.db import migrations, models


DEFAULT_ENTRY_PLANS = {
    "from-scratch": {
        "recommended_agents": ["structure", "character", "outline", "script", "review"],
        "hidden_agents": [],
        "default_params": {},
    },
    "from-outline": {
        "recommended_agents": ["character", "script", "review"],
        "hidden_agents": ["structure", "outline"],
        "default_params": {},
    },
    "from-reference": {
        "recommended_agents": ["structure", "outline", "script", "review"],
        "hidden_agents": [],
        "default_params": {},
    },
    "ip-sequel": {
        "recommended_agents": ["outline", "script", "review"],
        "hidden_agents": ["structure"],
        "default_params": {},
    },
    "novel-adaptation": {
        "recommended_agents": ["script", "review"],
        "hidden_agents": ["structure", "outline", "character"],
        "default_params": {},
    },
}


def seed_creation_entry_plans(apps, schema_editor):
    SkillConfigEntry = apps.get_model("skill", "SkillConfigEntry")
    SkillConfigEntry.objects.update_or_create(
        config_key="creation-entry-plans",
        defaults={
            "edition": "unified",
            "content": DEFAULT_ENTRY_PLANS,
            "version": "1.0.0",
            "note": "创作入口 → 推荐 Agent Plan（skill-agent/30-ENTRY-PLAN.md）",
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0037_skill_rule_item"),
    ]

    operations = [
        migrations.AddField(
            model_name="skillruleconfig",
            name="content_source",
            field=models.CharField(
                choices=[
                    ("json", "JSON 包"),
                    ("atomic", "原子条目"),
                    ("hybrid", "混合（条目优先）"),
                ],
                db_index=True,
                default="hybrid",
                help_text="json=仅 SkillRuleConfig；atomic=仅 SkillRuleItem；hybrid=条目优先、Config 兜底",
                max_length=16,
                verbose_name="内容来源",
            ),
        ),
        migrations.RunPython(seed_creation_entry_plans, migrations.RunPython.noop),
    ]
