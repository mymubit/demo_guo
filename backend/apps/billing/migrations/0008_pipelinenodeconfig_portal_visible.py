# -*- coding: utf-8 -*-
from django.db import migrations, models

_LEGACY_PORTAL_HIDDEN = ("node-6-review", "node-8-score")


def hide_legacy_review_score_nodes(apps, schema_editor):
    PipelineNodeConfig = apps.get_model("billing", "PipelineNodeConfig")
    PipelineNodeConfig.objects.filter(fusion_node_id__in=_LEGACY_PORTAL_HIDDEN).update(
        portal_visible=False
    )


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0007_rename_billing_coi_user_id_6a8fbd_idx_billing_coi_user_id_2625da_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="pipelinenodeconfig",
            name="portal_visible",
            field=models.BooleanField(
                default=True,
                help_text="关闭后不在创作页主链展示（后台仍可配置与执行）",
                verbose_name="C 端展示",
            ),
        ),
        migrations.RunPython(hide_legacy_review_score_nodes, migrations.RunPython.noop),
    ]
