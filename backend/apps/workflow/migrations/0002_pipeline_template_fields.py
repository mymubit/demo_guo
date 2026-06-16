# -*- coding: utf-8 -*-
from django.db import migrations, models


def backfill_pipeline_pack_meta(apps, schema_editor):
    FusionPipelinePack = apps.get_model("workflow", "FusionPipelinePack")
    for pack in FusionPipelinePack.objects.all():
        changed = False
        if not pack.display_name:
            pack.display_name = pack.version
            changed = True
        if pack.is_active and not pack.is_published_to_portal:
            pack.is_published_to_portal = True
            changed = True
        if pack.is_active and not pack.is_default_for_creation:
            if not FusionPipelinePack.objects.filter(is_default_for_creation=True).exists():
                pack.is_default_for_creation = True
                changed = True
        if changed:
            pack.save(
                update_fields=[
                    "display_name",
                    "is_published_to_portal",
                    "is_default_for_creation",
                    "updated_at",
                ]
            )


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="fusionpipelinepack",
            name="display_name",
            field=models.CharField(blank=True, default="", max_length=128, verbose_name="展示名称"),
        ),
        migrations.AddField(
            model_name="fusionpipelinepack",
            name="description",
            field=models.TextField(blank=True, default="", verbose_name="说明"),
        ),
        migrations.AddField(
            model_name="fusionpipelinepack",
            name="slug",
            field=models.SlugField(blank=True, max_length=64, null=True, unique=True, verbose_name="标识"),
        ),
        migrations.AddField(
            model_name="fusionpipelinepack",
            name="is_published_to_portal",
            field=models.BooleanField(db_index=True, default=False, verbose_name="创作入口可选"),
        ),
        migrations.AddField(
            model_name="fusionpipelinepack",
            name="is_default_for_creation",
            field=models.BooleanField(db_index=True, default=False, verbose_name="创作默认流水线"),
        ),
        migrations.AddField(
            model_name="fusionpipelinepack",
            name="flow_graph",
            field=models.JSONField(blank=True, default=dict, verbose_name="流程图画布"),
        ),
        migrations.AddField(
            model_name="fusionpipelinepack",
            name="post_script_chain",
            field=models.JSONField(blank=True, default=list, verbose_name="后处理 Agent 链"),
        ),
        migrations.AlterField(
            model_name="fusionpipelinepack",
            name="is_active",
            field=models.BooleanField(db_index=True, default=False, verbose_name="当前编辑中"),
        ),
        migrations.RunPython(backfill_pipeline_pack_meta, migrations.RunPython.noop),
    ]
