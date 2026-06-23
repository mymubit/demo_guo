# -*- coding: utf-8 -*-
# Generated migration: WorkflowTemplate 工作流模板表

import uuid
from django.db import migrations, models


_PRESET_TEMPLATES = [
    {
        "template_id": "tpl_standard_24ep",
        "name": "标准24集竖短剧",
        "description": "短剧创作标准流程，7节点串行执行：立项→世界观→人设→大纲→剧本→质检→评分",
        "is_system": True,
        "nodes": [
            {"index": 1, "agent_id": "brief",     "name": "立项策划",   "node_type": "agent_node"},
            {"index": 2, "agent_id": "world",     "name": "世界观架构", "node_type": "agent_node"},
            {"index": 3, "agent_id": "character", "name": "人设创作",   "node_type": "agent_node"},
            {"index": 4, "agent_id": "outline",   "name": "分集大纲",   "node_type": "agent_node"},
            {"index": 5, "agent_id": "script",    "name": "剧本正文",   "node_type": "agent_node"},
            {"index": 6, "agent_id": "review",    "name": "合规质检",   "node_type": "loop_node"},
            {"index": 7, "agent_id": "score",     "name": "质量评分",   "node_type": "agent_node"},
        ],
    },
    {
        "template_id": "tpl_quick_1min",
        "name": "1分钟爽文短剧",
        "description": "省略世界观与人设节点，快速生成简短剧本，适合单集/短视频场景",
        "is_system": True,
        "nodes": [
            {"index": 1, "agent_id": "brief",   "name": "立项策划", "node_type": "agent_node"},
            {"index": 2, "agent_id": "outline", "name": "极简大纲", "node_type": "agent_node"},
            {"index": 3, "agent_id": "script",  "name": "剧本正文", "node_type": "agent_node"},
            {"index": 4, "agent_id": "review",  "name": "合规质检", "node_type": "agent_node"},
        ],
    },
    {
        "template_id": "tpl_reversal_drama",
        "name": "逆袭题材强化模板",
        "description": "在标准7节点基础上，大纲环节加强反转设计，适合逆袭/爽文竖短剧",
        "is_system": True,
        "nodes": [
            {"index": 1, "agent_id": "brief",     "name": "立项策划",     "node_type": "agent_node"},
            {"index": 2, "agent_id": "world",     "name": "世界观架构",   "node_type": "agent_node"},
            {"index": 3, "agent_id": "character", "name": "人设创作",     "node_type": "agent_node"},
            {"index": 4, "agent_id": "outline",   "name": "分集大纲",     "node_type": "agent_node",
             "config": {"enhance_reversal": True}},
            {"index": 5, "agent_id": "script",    "name": "剧本正文",     "node_type": "agent_node"},
            {"index": 6, "agent_id": "review",    "name": "合规质检",     "node_type": "loop_node"},
            {"index": 7, "agent_id": "score",     "name": "质量评分",     "node_type": "agent_node"},
            {"index": 8, "agent_id": "marketing", "name": "营销素材生成", "node_type": "agent_node",
             "optional": True},
        ],
    },
]


def seed_templates(apps, schema_editor):
    WorkflowTemplate = apps.get_model("workflow", "WorkflowTemplate")
    for tpl in _PRESET_TEMPLATES:
        WorkflowTemplate.objects.get_or_create(
            template_id=tpl["template_id"],
            defaults={
                "name":        tpl["name"],
                "description": tpl["description"],
                "nodes":       tpl["nodes"],
                "is_system":   tpl["is_system"],
                "created_by":  "system",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0003_fusionpipelinepack_version_management'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('template_id', models.CharField(
                    db_index=True, max_length=64,
                    help_text='如 tpl_standard_24ep / tpl_quick_1min',
                    unique=True, verbose_name='模板 ID',
                )),
                ('name', models.CharField(max_length=128, verbose_name='模板名称')),
                ('description', models.TextField(blank=True, default='', verbose_name='模板说明')),
                ('nodes', models.JSONField(
                    default=list,
                    help_text='数组，每项描述一个工作流节点（agent_id/node_type/config 等）',
                    verbose_name='节点配置',
                )),
                ('is_system', models.BooleanField(
                    default=False,
                    help_text='True=系统预置模板（不可删除）；False=用户/运营自定义',
                    verbose_name='系统预置',
                )),
                ('created_by', models.CharField(blank=True, default='system', max_length=128, verbose_name='创建人')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '工作流模板',
                'verbose_name_plural': '工作流模板',
                'db_table': 'workflow_template',
                'ordering': ['-is_system', 'name'],
            },
        ),
        migrations.RunPython(seed_templates, migrations.RunPython.noop),
    ]
