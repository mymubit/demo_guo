# Generated manually — 主链步骤已合并至 skill.FusionPipelineNode
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0008_pipelinenodeconfig_portal_visible"),
    ]

    operations = [
        migrations.DeleteModel(
            name="PipelineNodeConfig",
        ),
    ]
