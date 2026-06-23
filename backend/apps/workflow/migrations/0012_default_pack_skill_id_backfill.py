# -*- coding: utf-8 -*-
# 数据修正：把默认 short-drama-v1 pack 中 5 个创作节点的 skill_id 补齐
# 历史数据创建时 skill_id 为空、runner_path 指向旧 workspace_bridge，
# 新引擎 SkillBridge 现优先按 skill_id 路由到 SkillInvoker。
# 此迁移幂等：仅在 skill_id 为空时才覆盖。
from django.db import migrations

# 默认 pack 节点 → skill_id 映射
NODE_SKILL_MAP = {
    "node_brief": "creation.brief",
    "node_structure": "creation.structure",
    "node_character": "creation.character",
    "node_outline": "creation.outline",
    "node_script": "creation.script",
}


def _backfill_skill_id(apps, schema_editor):
    FusionPipelineNode = apps.get_model("workflow", "FusionPipelineNode")
    for fusion_node_id, skill_id in NODE_SKILL_MAP.items():
        qs = FusionPipelineNode.objects.filter(
            fusion_node_id=fusion_node_id,
        )
        # 仅在 skill_id 为空或已被 workspace_bridge 占用时回填
        updated = qs.filter(skill_id="").update(skill_id=skill_id)
        if updated:
            print(
                f"[0012] backfill skill_id fusion_node_id={fusion_node_id} "
                f"-> {skill_id} count={updated}",
            )


def _rollback_skill_id(apps, schema_editor):
    FusionPipelineNode = apps.get_model("workflow", "FusionPipelineNode")
    for fusion_node_id, skill_id in NODE_SKILL_MAP.items():
        FusionPipelineNode.objects.filter(
            fusion_node_id=fusion_node_id,
            skill_id=skill_id,
        ).update(skill_id="")


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0011_node_execution_retry_and_refund"),
    ]

    operations = [
        migrations.RunPython(_backfill_skill_id, _rollback_skill_id),
    ]
