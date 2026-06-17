# P0-3 阶段：为 FusionPipelineNode 新增 skill_id 字段，
# 用于 SkillBridge 路由（通过 skill_id 找到 AgentSkillDefinition 并调用 LLM）。
#
# 节点注册示例：
#   FusionPipelineNode(skill_id="creation.brief", runner_type="fusion_node", ...)
#     → SkillBridge 路由到 SkillInvoker.invoke("creation.brief", ...)
#   FusionPipelineNode(runner_path="apps.creation.orchestration.brief.run", ...)
#     → SkillBridge 按路径动态调用 Python 函数
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0008_workflow_instance_and_node_execution_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="fusionpipelinenode",
            name="skill_id",
            field=models.CharField(
                "技能 ID",
                max_length=128,
                blank=True,
                default="",
                db_index=True,
                help_text=(
                    "技能标识，用于 SkillBridge 路由。"
                    "例：creation.brief / fusion.skill.review"
                ),
            ),
        ),
        # 补充 runner_path 索引（用于快速路由）
        migrations.AddIndex(
            model_name="fusionpipelinenode",
            index=models.Index(
                fields=["pack", "skill_id"],
                name="node_pack_skill_idx",
            ),
        ),
    ]
