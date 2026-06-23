# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0018_sub_skill_io_payload"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentexecutionrun",
            name="agent_version",
            field=models.CharField(blank=True, default="", max_length=32, verbose_name="Agent 版本"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="completion_tokens",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Completion Tokens"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="estimated_prompt_tokens",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="预估 Prompt Tokens"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="input_artifact_keys",
            field=models.JSONField(blank=True, default=list, verbose_name="输入产物键"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="input_snapshot",
            field=models.JSONField(blank=True, default=dict, verbose_name="输入快照"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="model_name",
            field=models.CharField(blank=True, default="", max_length=128, verbose_name="模型"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="output_artifact_keys",
            field=models.JSONField(blank=True, default=list, verbose_name="输出产物键"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="overwrite_mode",
            field=models.CharField(blank=True, default="replace", max_length=16, verbose_name="覆盖模式"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="prompt_tokens",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Prompt Tokens"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="prompt_version",
            field=models.CharField(blank=True, default="", max_length=32, verbose_name="Prompt 版本"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="provider_name",
            field=models.CharField(blank=True, default="", max_length=128, verbose_name="Provider"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="rendered_prompt_preview",
            field=models.TextField(blank=True, default="", verbose_name="Prompt 预览"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="run_params",
            field=models.JSONField(blank=True, default=dict, verbose_name="运行参数"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="started_by",
            field=models.CharField(blank=True, default="user", max_length=16, verbose_name="触发方"),
        ),
        migrations.AddField(
            model_name="agentexecutionrun",
            name="total_tokens",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Total Tokens"),
        ),
    ]
