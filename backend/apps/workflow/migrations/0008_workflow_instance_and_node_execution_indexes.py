# P0-1 阶段：为 workflow_instance 和 workflow_node_execution 补充生产级复合索引，
# 以及 FusionPipelinePack 的 is_active + pack_status 复合索引（管理后台查询优化）。
#
# 索引策略：
#   workflow_instance:
#     - (pack_id, status, -created_at)：管理后台「按 pack 筛选 + 状态 + 时间排序」
#     - (user_id, -created_at)：用户「我的创作列表」
#     - (trigger_type, -created_at)：触发类型分布统计
#
#   workflow_node_execution:
#     - (instance_id, -started_at)：实例详情页「节点 timeline（按时间正序）」
#     - (runner_type, status)：节点健康度监控（某类节点失败率）
#
#   skill_fusion_pipeline_pack:
#     - (is_active, is_published_to_portal)：C 端创作入口可选 pack 快速查询
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0007_workflow_instance_and_node_execution"),
    ]

    operations = [

        # ── workflow_instance 补充索引 ──────────────────────────────
        migrations.AddIndex(
            model_name="workflowinstance",
            index=models.Index(
                fields=["pack", "status", "-created_at"],
                name="inst_pack_stat_dt_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="workflowinstance",
            index=models.Index(
                fields=["user_id", "-created_at"],
                name="inst_user_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="workflowinstance",
            index=models.Index(
                fields=["trigger_type", "-created_at"],
                name="inst_trigger_created_idx",
            ),
        ),

        # ── workflow_node_execution 补充索引 ───────────────────────
        migrations.AddIndex(
            model_name="nodeexecution",
            index=models.Index(
                fields=["instance", "-started_at"],
                name="ne_inst_started_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="nodeexecution",
            index=models.Index(
                fields=["runner_type", "status"],
                name="ne_runner_status_idx",
            ),
        ),

        # ── FusionPipelinePack 补充 is_active 索引 ─────────────────
        migrations.AddIndex(
            model_name="fusionpipelinepack",
            index=models.Index(
                fields=["is_active", "is_published_to_portal"],
                name="pack_active_portal_idx",
            ),
        ),

        # ── FusionPipelineNode 补充 enabled + chain_order 索引 ────
        # （仅对 enabled=True 的节点做查询，可以过滤掉已禁用节点）
        migrations.AddIndex(
            model_name="fusionpipelinenode",
            index=models.Index(
                fields=["pack", "enabled", "chain_order"],
                name="node_pack_en_order_idx",
            ),
        ),
    ]
