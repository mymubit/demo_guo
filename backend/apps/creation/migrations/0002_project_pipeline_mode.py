# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="pipeline_mode",
            field=models.CharField(
                choices=[("auto", "一键生成"), ("step", "分步掌控")],
                default="auto",
                help_text="auto=一键跑完；step=每节点暂停待确认",
                max_length=8,
                verbose_name="流水线模式",
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "排队中"),
                    ("running", "创作中"),
                    ("awaiting", "待确认"),
                    ("completed", "已完成"),
                    ("failed", "失败"),
                ],
                default="pending",
                max_length=16,
                verbose_name="状态",
            ),
        ),
    ]
