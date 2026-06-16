# Generated migration: AgentSkillDefinition 灰度分流与兼容性字段扩展

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('skill', '0029_agentskilldefinition_lifecycle_fields'),
    ]

    operations = [
        # 新增：灰度分流稳定哈希种子
        migrations.AddField(
            model_name='agentskilldefinition',
            name='gray_traffic_salt',
            field=models.CharField(
                blank=True, default='',
                help_text='用于 gray_traffic_salt + user_id % 100 < gray_weight 稳定分流',
                max_length=32, verbose_name='灰度分流种子',
            ),
        ),
        # 新增：声明该技能依赖的最低 LLM 版本
        migrations.AddField(
            model_name='agentskilldefinition',
            name='min_llm_version',
            field=models.CharField(
                blank=True, default='',
                help_text='如 gpt-4o-mini-2024-07-18，低于此版本拒绝调用',
                max_length=64, verbose_name='最低 LLM 版本',
            ),
        ),
        # 新增：适用场景标签
        migrations.AddField(
            model_name='agentskilldefinition',
            name='tags',
            field=models.JSONField(
                blank=True, default=list,
                help_text='如 ["短剧", "逆袭题材", "1分钟"]',
                verbose_name='适用场景标签',
            ),
        ),
        # 新增索引：lifecycle_status + gray_weight 组合索引
        migrations.AddIndex(
            model_name='agentskilldefinition',
            index=models.Index(
                fields=['lifecycle_status', 'gray_weight'],
                name='skill_def_status_gray_idx',
            ),
        ),
    ]
