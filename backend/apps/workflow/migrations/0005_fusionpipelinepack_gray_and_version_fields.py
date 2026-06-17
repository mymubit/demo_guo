# Generated migration: FusionPipelinePack 灰度分流与 LLM 版本兼容性字段扩展

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0004_workflow_template'),
    ]

    operations = [
        # 新增：灰度分流稳定哈希种子
        migrations.AddField(
            model_name='fusionpipelinepack',
            name='gray_traffic_salt',
            field=models.CharField(
                blank=True, default='',
                help_text='用于 gray_traffic_salt + user_id % 100 < gray_weight 稳定分流',
                max_length=32, verbose_name='灰度分流种子',
            ),
        ),
        # 新增：声明该流水线依赖的最低 LLM 配置版本
        migrations.AddField(
            model_name='fusionpipelinepack',
            name='min_llm_provider_version',
            field=models.CharField(
                blank=True, default='',
                help_text='用于兼容性校验，低于此版本拒绝使用此流水线',
                max_length=64, verbose_name='最低 LLM Provider 版本',
            ),
        ),
        # 新增索引：pack_status + gray_weight 组合索引
        migrations.AddIndex(
            model_name='fusionpipelinepack',
            index=models.Index(
                fields=['pack_status', 'gray_weight'],
                name='pack_status_gray_idx',
            ),
        ),
    ]
