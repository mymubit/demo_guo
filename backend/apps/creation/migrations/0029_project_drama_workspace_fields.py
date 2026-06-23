# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0028_remove_legacy_pipeline_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="track_mode",
            field=models.CharField(
                blank=True,
                default="",
                help_text="fast / expert；空表示非 Drama 工作台项目",
                max_length=16,
                verbose_name="创作轨道",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="drama_stage",
            field=models.CharField(
                blank=True,
                default="strategy",
                help_text="Drama 工作台阶段代码",
                max_length=32,
                verbose_name="Drama 当前阶段",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="completed_roles",
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name="已完成 Drama 角色",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="word_count_stats",
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name="分集字数统计",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="quality_scores",
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name="Drama 8维评分",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="delivery_status",
            field=models.CharField(
                blank=True,
                default="pending",
                help_text="pending / ready / delivered",
                max_length=16,
                verbose_name="交付状态",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="total_tokens_used",
            field=models.IntegerField(default=0, verbose_name="累计 Token 消耗"),
        ),
        migrations.AddField(
            model_name="project",
            name="total_cost_cents",
            field=models.IntegerField(default=0, verbose_name="累计费用（分）"),
        ),
    ]
