# -*- coding: utf-8 -*-
from django.db import migrations


def migrate_pipeline_skill_to_agents(apps, schema_editor):
    return  # drama.* 新体系，已废弃

    from apps.agent.routes import AgentLlmRouteService
    from apps.agent.registry import AgentRegistryConfigService

    AgentLlmRouteService.seed_defaults()
    AgentRegistryConfigService.migrate_pipeline_skill_config()


class Migration(migrations.Migration):
    dependencies = [
        ("skill", "0025_reference_library_review_min_sub"),
    ]

    operations = [
        migrations.RunPython(migrate_pipeline_skill_to_agents, migrations.RunPython.noop),
        migrations.RemoveField(model_name="fusionpipelinenode", name="sub_skill"),
        migrations.RemoveField(model_name="fusionpipelinenode", name="tier1_sections"),
        migrations.RemoveField(model_name="fusionpipelinenode", name="system_prompt"),
        migrations.RemoveField(model_name="fusionpipelinenode", name="user_prompt_tpl"),
        migrations.RemoveField(model_name="fusionpipelinenode", name="prompt_constraints"),
        migrations.RemoveField(model_name="fusionpipelinenode", name="prompt_enabled"),
        migrations.RemoveField(model_name="fusionpipelinenode", name="llm_provider"),
        migrations.RemoveField(model_name="fusionpipelinenode", name="max_tokens"),
    ]
