# Generated manually — 主链 LLM 配置已合并至 FusionPipelineNode
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0023_fusionpipelinenode_unified_step_config"),
    ]

    operations = [
        migrations.DeleteModel(
            name="FusionNodeLlmPromptConfig",
        ),
    ]
