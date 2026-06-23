# -*- coding: utf-8 -*-
# Generated migration: CreationTask 统一任务表 + Project 状态同步

import uuid
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creation', '0013_project_pipeline_pack'),
        ('workflow', '0003_fusionpipelinepack_version_management'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreationTask',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('trigger_mode', models.CharField(
                    choices=[('auto', '一键生成'), ('step', '分步掌控'), ('workspace', '技能工作台'), ('retry', '人工重试')],
                    default='workspace', max_length=16, verbose_name='触发模式',
                )),
                ('state', models.CharField(
                    choices=[('pending', '待执行'), ('running', '执行中'), ('paused', '已暂停'),
                             ('completed', '已完成'), ('failed', '已失败'), ('retrying', '重试中'),
                             ('cancelled', '已取消')],
                    db_index=True, default='pending', max_length=16, verbose_name='执行状态',
                )),
                ('current_node_index', models.IntegerField(default=0, verbose_name='当前节点')),
                ('progress_percent', models.PositiveSmallIntegerField(default=0, verbose_name='进度（%）')),
                ('celery_task_id', models.CharField(blank=True, default='', max_length=255, verbose_name='Celery Task ID')),
                ('error_code', models.CharField(blank=True, default='', max_length=64, verbose_name='错误码')),
                ('error_message', models.TextField(blank=True, default='', verbose_name='错误信息')),
                ('retry_count', models.PositiveSmallIntegerField(default=0, verbose_name='重试次数')),
                ('extra', models.JSONField(
                    blank=True, default=dict,
                    help_text='存储 node_index、options 等调用参数快照，便于重试恢复',
                    verbose_name='扩展参数',
                )),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tasks', to='creation.project', verbose_name='所属项目',
                )),
                ('workflow', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='tasks', to='workflow.fusionpipelinepack', verbose_name='工作流版本',
                )),
            ],
            options={
                'verbose_name': '创作任务',
                'verbose_name_plural': '创作任务',
                'db_table': 'creation_task',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['project', 'state'], name='task_project_state_idx'),
                    models.Index(fields=['state', '-created_at'], name='task_state_time_idx'),
                ],
            },
        ),
    ]
