# -*- coding: utf-8 -*-
# P1 阶段：为 FusionPipelineNode 增加 extra_config 字段与三类编排 runner_type
#
# 背景：
# - 编排层 P1 阶段需要支持 PARALLEL / ITERATE / HUMAN 三类节点；
# - 这三类节点都需要读取节点扩展配置（group_key / max_attempts / 条件 / 提示语等），
#   在 FusionPipelineNode 上新增 extra_config JSONField 承载这些配置。
# - 同时为 RUNNER_TYPE_CHOICES 追加三个枚举值（parallel_group / iterate_loop / human_gate）。

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0005_fusionpipelinepack_gray_and_version_fields'),
    ]

    operations = [
        # 1) 扩展 runner_type 枚举：新增 parallel_group / iterate_loop / human_gate
        migrations.AlterField(
            model_name='fusionpipelinenode',
            name='runner_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('fusion_node', '融合主链节点'),
                    ('fusion_review', '融合质检'),
                    ('fusion_score', '融合评分'),
                    ('agent_chain', 'Agent 后处理链'),
                    ('parallel_group', '并行节点组（同级并发）'),
                    ('iterate_loop', '迭代循环节点'),
                    ('human_gate', '人工门控节点（分步确认）'),
                ],
                default='',
                max_length=32,
                verbose_name='执行器类型',
            ),
        ),
        # 2) 新增 extra_config JSONField：承载 PARALLEL/ITERATE/HUMAN 节点的差异化配置
        migrations.AddField(
            model_name='fusionpipelinenode',
            name='extra_config',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    '用于 PARALLEL/ITERATE/HUMAN 节点的差异化配置，结构见字段说明'
                ),
                verbose_name='节点扩展配置',
            ),
        ),
    ]
