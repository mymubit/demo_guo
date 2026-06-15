# Generated manually for agent execution tracing

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("creation", "0003_project_workspace_mode"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AgentExecutionRun",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("agent_id", models.CharField(db_index=True, max_length=64, verbose_name="Agent ID")),
                (
                    "node_index",
                    models.PositiveSmallIntegerField(
                        blank=True, db_index=True, null=True, verbose_name="节点序号"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("running", "执行中"),
                            ("completed", "成功"),
                            ("failed", "失败"),
                            ("partial", "部分成功"),
                        ],
                        db_index=True,
                        default="running",
                        max_length=16,
                        verbose_name="状态",
                    ),
                ),
                ("batch_from", models.PositiveIntegerField(blank=True, null=True, verbose_name="批次起始")),
                ("batch_to", models.PositiveIntegerField(blank=True, null=True, verbose_name="批次结束")),
                (
                    "outline_mode",
                    models.CharField(blank=True, default="", max_length=32, verbose_name="大纲模式"),
                ),
                ("input_summary", models.JSONField(blank=True, default=dict, verbose_name="输入摘要")),
                ("output_summary", models.JSONField(blank=True, default=dict, verbose_name="输出摘要")),
                (
                    "output_artifact_key",
                    models.CharField(blank=True, default="", max_length=64, verbose_name="产出键"),
                ),
                ("error_message", models.TextField(blank=True, default="", verbose_name="错误信息")),
                (
                    "started_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        verbose_name="开始时间",
                    ),
                ),
                ("finished_at", models.DateTimeField(blank=True, null=True, verbose_name="结束时间")),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agent_execution_runs",
                        to="creation.project",
                        verbose_name="项目",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agent_execution_runs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "Agent 执行记录",
                "verbose_name_plural": "Agent 执行记录",
                "db_table": "creation_agent_execution_run",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="SubSkillExecutionLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("skill_id", models.CharField(db_index=True, max_length=128, verbose_name="子技能 ID")),
                ("skill_type", models.CharField(blank=True, default="", max_length=32, verbose_name="类型")),
                ("cli", models.CharField(blank=True, default="", max_length=64, verbose_name="CLI")),
                ("script", models.CharField(blank=True, default="", max_length=128, verbose_name="脚本")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("executed", "已执行"),
                            ("failed", "失败"),
                            ("skipped", "跳过"),
                        ],
                        db_index=True,
                        max_length=16,
                        verbose_name="状态",
                    ),
                ),
                ("attempt", models.PositiveSmallIntegerField(default=1, verbose_name="尝试次数")),
                ("order_index", models.PositiveSmallIntegerField(default=0, verbose_name="顺序")),
                ("input_summary", models.JSONField(blank=True, default=dict, verbose_name="输入摘要")),
                ("output_summary", models.JSONField(blank=True, default=dict, verbose_name="输出摘要")),
                ("error_message", models.TextField(blank=True, default="", verbose_name="错误信息")),
                ("duration_ms", models.PositiveIntegerField(blank=True, null=True, verbose_name="耗时(ms)")),
                (
                    "started_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="开始时间"),
                ),
                ("finished_at", models.DateTimeField(blank=True, null=True, verbose_name="结束时间")),
                (
                    "run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sub_skill_logs",
                        to="creation.agentexecutionrun",
                        verbose_name="执行记录",
                    ),
                ),
            ],
            options={
                "verbose_name": "子技能执行记录",
                "verbose_name_plural": "子技能执行记录",
                "db_table": "creation_sub_skill_execution_log",
                "ordering": ["order_index", "started_at"],
            },
        ),
        migrations.AddIndex(
            model_name="agentexecutionrun",
            index=models.Index(fields=["project", "-started_at"], name="creation_ag_project_8d0f2d_idx"),
        ),
        migrations.AddIndex(
            model_name="agentexecutionrun",
            index=models.Index(fields=["agent_id", "-started_at"], name="creation_ag_agent_i_6b8a11_idx"),
        ),
        migrations.AddIndex(
            model_name="subskillexecutionlog",
            index=models.Index(fields=["run", "order_index"], name="creation_su_run_id_0f6d84_idx"),
        ),
        migrations.AddIndex(
            model_name="subskillexecutionlog",
            index=models.Index(fields=["skill_id", "-started_at"], name="creation_su_skill_i_2c0b9a_idx"),
        ),
        migrations.AddConstraint(
            model_name="subskillexecutionlog",
            constraint=models.UniqueConstraint(
                fields=("run", "skill_id"),
                name="uniq_sub_skill_per_run",
            ),
        ),
    ]
