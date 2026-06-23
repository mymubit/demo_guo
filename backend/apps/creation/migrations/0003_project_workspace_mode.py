# -*- coding: utf-8 -*-
# Generated manually for workspace skill mode

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0002_project_pipeline_mode"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="pipeline_mode",
            field=models.CharField(
                choices=[
                    ("auto", "一键生成"),
                    ("step", "分步掌控"),
                    ("workspace", "技能工作台"),
                ],
                default="workspace",
                help_text="workspace=按技能模块；auto=一键跑完；step=每节点暂停待确认",
                max_length=16,
                verbose_name="流水线模式",
            ),
        ),
    ]
