# -*- coding: utf-8 -*-
# Generated migration: AgentSkillDefinition 生命周期与调用协议字段扩展

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('skill', '0028_agentskilldefinition_skillconfigentry_skilldefect'),
    ]

    operations = [
        # 三层分类
        migrations.AddField(
            model_name='agentskilldefinition',
            name='skill_layer',
            field=models.CharField(
                blank=True, choices=[('foundation', '基础能力层'), ('business', '业务技能层'), ('tool', '工具能力层')],
                db_index=True, default='', help_text='foundation=基础能力层；business=业务技能层；tool=工具能力层',
                max_length=20, verbose_name='技能层级',
            ),
        ),
        migrations.AddField(
            model_name='agentskilldefinition',
            name='sub_category',
            field=models.CharField(
                blank=True, default='',
                help_text='如 人设/大纲/剧本/审核 等，用于技能库细粒度筛选',
                max_length=64, verbose_name='子分类',
            ),
        ),
        # 生命周期
        migrations.AddField(
            model_name='agentskilldefinition',
            name='lifecycle_status',
            field=models.CharField(
                choices=[('draft', '草稿'), ('active', '上线'), ('gray', '灰度'), ('deprecated', '废弃')],
                db_index=True, default='draft', max_length=16, verbose_name='生命周期状态',
            ),
        ),
        migrations.AddField(
            model_name='agentskilldefinition',
            name='gray_weight',
            field=models.PositiveSmallIntegerField(
                default=100,
                help_text='0-100，灰度模式下按此比例分流；100=全量，0=不分流',
                verbose_name='灰度权重',
            ),
        ),
        migrations.AddField(
            model_name='agentskilldefinition',
            name='published_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='发布时间'),
        ),
        migrations.AddField(
            model_name='agentskilldefinition',
            name='deprecated_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='废弃时间'),
        ),
        # 调用协议
        migrations.AddField(
            model_name='agentskilldefinition',
            name='input_schema',
            field=models.JSONField(
                blank=True, default=dict,
                help_text='描述技能入参结构，用于参数校验与 Admin 编辑界面',
                verbose_name='入参 Schema（JSONSchema）',
            ),
        ),
        migrations.AddField(
            model_name='agentskilldefinition',
            name='output_schema',
            field=models.JSONField(
                blank=True, default=dict,
                help_text='描述技能出参结构，用于下游消费校验',
                verbose_name='出参 Schema（JSONSchema）',
            ),
        ),
        migrations.AddField(
            model_name='agentskilldefinition',
            name='system_hint',
            field=models.TextField(
                blank=True, default='',
                help_text='取代 _SUB_SKILL_SYSTEM_HINTS 硬编码，由 Admin 可编辑的 LLM 系统提示词',
                verbose_name='System Hint（Prompt）',
            ),
        ),
        # 执行策略
        migrations.AddField(
            model_name='agentskilldefinition',
            name='timeout_seconds',
            field=models.PositiveSmallIntegerField(
                default=60,
                help_text='单次技能调用最大等待时间，超时触发 retry_policy',
                verbose_name='超时时间（秒）',
            ),
        ),
        migrations.AddField(
            model_name='agentskilldefinition',
            name='quota_cost',
            field=models.DecimalField(
                decimal_places=4, default=0, max_digits=10,
                help_text='每次调用消耗的配额单位，0 表示免费',
                verbose_name='配额消耗',
            ),
        ),
        migrations.AddField(
            model_name='agentskilldefinition',
            name='retry_policy',
            field=models.JSONField(
                blank=True, default=dict,
                help_text='如 {"max_attempts": 2, "backoff_seconds": 5}',
                verbose_name='重试策略',
            ),
        ),
        migrations.AddField(
            model_name='agentskilldefinition',
            name='fallback_skill_id',
            field=models.CharField(
                blank=True, default='', max_length=100,
                help_text='主技能失败时的降级技能 skill_id，为空表示不降级',
                verbose_name='降级技能 ID',
            ),
        ),
        # 更新排序与索引
        migrations.AlterModelOptions(
            name='agentskilldefinition',
            options={
                'ordering': ['skill_layer', 'category', 'skill_id'],
                'verbose_name': 'Agent 技能定义',
                'verbose_name_plural': 'Agent 技能定义',
            },
        ),
        migrations.AddIndex(
            model_name='agentskilldefinition',
            index=models.Index(
                fields=['lifecycle_status', 'skill_layer'],
                name='skill_def_status_layer_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='agentskilldefinition',
            index=models.Index(
                fields=['skill_layer', 'sub_category'],
                name='skill_def_layer_subcat_idx',
            ),
        ),
        # 将现有 is_active=True 的记录的 lifecycle_status 初始化为 active
        migrations.RunSQL(
            sql="UPDATE skill_agent_definition SET lifecycle_status = 'active' WHERE is_active = TRUE",
            reverse_sql="UPDATE skill_agent_definition SET lifecycle_status = 'draft'",
        ),
    ]
