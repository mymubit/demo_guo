"""A/B 实验模块初始迁移。"""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0003_ticket_default_categories"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Experiment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.SlugField(help_text="实验唯一 key（代码层引用）", max_length=64, unique=True)),
                ("name", models.CharField(max_length=128)),
                ("description", models.TextField(blank=True, default="")),
                ("hypothesis", models.TextField(blank=True, default="")),
                ("bucket", models.CharField(
                    choices=[("skill", "技能"), ("pipeline", "工作流"),
                             ("config", "配置项"), ("copy", "文案"),
                             ("pricing", "定价")],
                    default="config", max_length=16,
                )),
                ("status", models.CharField(
                    choices=[("draft", "草稿"), ("running", "进行中"),
                             ("paused", "暂停"), ("concluded", "已结束"),
                             ("abandoned", "废弃")],
                    default="draft", max_length=16,
                )),
                ("target_filter", models.JSONField(default=dict)),
                ("traffic_allocation", models.PositiveIntegerField(default=100)),
                ("salt", models.CharField(default="default", max_length=32)),
                ("primary_metric", models.CharField(blank=True, default="", max_length=64)),
                ("secondary_metrics", models.JSONField(default=list)),
                ("min_sample_size", models.PositiveIntegerField(default=0)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("conclusion", models.TextField(blank=True, default="")),
                ("winner_variant", models.CharField(blank=True, default="", max_length=64)),
                ("operator", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "ops_experiment"},
        ),
        migrations.AddIndex(
            model_name="experiment",
            index=models.Index(fields=["status", "-created_at"], name="ops_exp_idx_status_created"),
        ),
        migrations.AddIndex(
            model_name="experiment",
            index=models.Index(fields=["bucket", "status"], name="ops_exp_idx_bucket_status"),
        ),
        migrations.CreateModel(
            name="Variant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=64)),
                ("name", models.CharField(max_length=64)),
                ("is_control", models.BooleanField(default=False)),
                ("weight", models.PositiveIntegerField(default=50)),
                ("payload", models.JSONField(default=dict)),
                ("description", models.TextField(blank=True, default="")),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("experiment", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="variants", to="operations.experiment",
                )),
            ],
            options={"db_table": "ops_experiment_variant", "ordering": ["sort_order", "id"]},
        ),
        migrations.AlterUniqueTogether(
            name="variant",
            unique_together={("experiment", "key")},
        ),
        migrations.AddIndex(
            model_name="variant",
            index=models.Index(fields=["experiment", "is_control"], name="ops_var_idx_exp_ctrl"),
        ),
        migrations.CreateModel(
            name="Assignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("anonymous_id", models.CharField(blank=True, default="", max_length=64)),
                ("variant_key", models.CharField(max_length=64)),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("experiment", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="assignments", to="operations.experiment",
                )),
                ("user", models.ForeignKey(
                    blank=True, null=True, on_delete=models.deletion.CASCADE,
                    related_name="experiment_assignments", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"db_table": "ops_experiment_assignment"},
        ),
        migrations.AlterUniqueTogether(
            name="assignment",
            unique_together={("experiment", "user"), ("experiment", "anonymous_id")},
        ),
        migrations.AddIndex(
            model_name="assignment",
            index=models.Index(fields=["experiment", "variant_key"], name="ops_asn_idx_exp_var"),
        ),
        migrations.AddIndex(
            model_name="assignment",
            index=models.Index(fields=["-assigned_at"], name="ops_asn_idx_assigned"),
        ),
        migrations.CreateModel(
            name="ExposureLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("anonymous_id", models.CharField(blank=True, default="", max_length=64)),
                ("surface", models.CharField(max_length=64)),
                ("context", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("experiment", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="exposures", to="operations.experiment",
                )),
                ("user", models.ForeignKey(
                    blank=True, null=True, on_delete=models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
                ("variant", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="exposures", to="operations.variant",
                )),
            ],
            options={"db_table": "ops_experiment_exposure"},
        ),
        migrations.AddIndex(
            model_name="exposurelog",
            index=models.Index(
                fields=["experiment", "variant", "-created_at"],
                name="ops_exp_log_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="exposurelog",
            index=models.Index(fields=["-created_at"], name="ops_exp_log_idx_created"),
        ),
        migrations.CreateModel(
            name="ConversionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("anonymous_id", models.CharField(blank=True, default="", max_length=64)),
                ("metric", models.CharField(max_length=64)),
                ("value", models.DecimalField(decimal_places=4, default=1, max_digits=12)),
                ("surface", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("experiment", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="conversions", to="operations.experiment",
                )),
                ("user", models.ForeignKey(
                    blank=True, null=True, on_delete=models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
                ("variant", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="conversions", to="operations.variant",
                )),
            ],
            options={"db_table": "ops_experiment_conversion"},
        ),
        migrations.AddIndex(
            model_name="conversionlog",
            index=models.Index(
                fields=["experiment", "metric", "-created_at"],
                name="ops_conv_log_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="conversionlog",
            index=models.Index(
                fields=["variant", "metric", "-created_at"],
                name="ops_conv_var_idx",
            ),
        ),
        migrations.CreateModel(
            name="ExperimentMetricSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("metric", models.CharField(max_length=64)),
                ("snapshot_date", models.DateField()),
                ("exposure_count", models.PositiveIntegerField(default=0)),
                ("conversion_count", models.PositiveIntegerField(default=0)),
                ("conversion_value_sum", models.DecimalField(decimal_places=4, default=0, max_digits=18)),
                ("extra", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("experiment", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="metric_snapshots", to="operations.experiment",
                )),
                ("variant", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="metric_snapshots", to="operations.variant",
                )),
            ],
            options={"db_table": "ops_experiment_metric_snapshot"},
        ),
        migrations.AlterUniqueTogether(
            name="experimentmetricsnapshot",
            unique_together={("experiment", "variant", "metric", "snapshot_date")},
        ),
        migrations.AddIndex(
            model_name="experimentmetricsnapshot",
            index=models.Index(
                fields=["experiment", "metric", "snapshot_date"],
                name="ops_ems_idx_exp_met_dt",
            ),
        ),
    ]
