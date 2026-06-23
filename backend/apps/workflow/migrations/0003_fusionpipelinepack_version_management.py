# -*- coding: utf-8 -*-
# Generated migration: FusionPipelinePack 版本管理字段扩展

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0002_pipeline_template_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='fusionpipelinepack',
            name='pack_status',
            field=models.CharField(
                choices=[('draft', '草稿'), ('active', '全量发布'), ('gray', '灰度'), ('archived', '已归档')],
                db_index=True, default='draft', max_length=16,
                help_text='draft=草稿；active=全量发布；gray=灰度；archived=已归档',
                verbose_name='发布状态',
            ),
        ),
        migrations.AddField(
            model_name='fusionpipelinepack',
            name='gray_weight',
            field=models.PositiveSmallIntegerField(
                default=100,
                help_text='0-100，pack_status=gray 时按此比例分流新创作项目',
                verbose_name='灰度权重',
            ),
        ),
        migrations.AddField(
            model_name='fusionpipelinepack',
            name='change_notes',
            field=models.TextField(blank=True, default='', verbose_name='变更说明'),
        ),
        migrations.AddField(
            model_name='fusionpipelinepack',
            name='published_by',
            field=models.CharField(
                blank=True, default='', max_length=128,
                help_text='记录发布操作人用户名', verbose_name='发布人',
            ),
        ),
        migrations.AddField(
            model_name='fusionpipelinepack',
            name='published_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='发布时间'),
        ),
        migrations.AddField(
            model_name='fusionpipelinepack',
            name='rollback_to',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='rollback_targets',
                to='workflow.fusionpipelinepack',
                verbose_name='回滚目标包',
            ),
        ),
        # 将现有 is_active=True 的包初始化为 active 状态
        migrations.RunSQL(
            sql="UPDATE skill_fusion_pipeline_pack SET pack_status = 'active' WHERE is_active = TRUE",
            reverse_sql="UPDATE skill_fusion_pipeline_pack SET pack_status = 'draft'",
        ),
    ]
