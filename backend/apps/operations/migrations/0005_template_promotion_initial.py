"""模板沉淀模块初始迁移。"""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0004_experiment_initial"),
        ("creation", "__first__"),
        ("workflow", "__first__"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TemplatePromotion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128)),
                ("description", models.TextField(blank=True, default="")),
                ("category", models.CharField(blank=True, default="", max_length=64)),
                ("tags", models.JSONField(default=list)),
                ("cover_url", models.CharField(blank=True, default="", max_length=512)),
                ("highlights", models.JSONField(default=list)),
                ("metric_snapshot", models.JSONField(default=dict)),
                ("status", models.CharField(
                    choices=[("candidate", "候选"), ("reviewing", "审核中"),
                             ("approved", "已通过"), ("published", "已上架"),
                             ("rejected", "已驳回"), ("archived", "已归档")],
                    default="candidate", max_length=16,
                )),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("review_note", models.TextField(blank=True, default="")),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.ForeignKey(
                    blank=True, null=True, on_delete=models.deletion.CASCADE,
                    related_name="promotions", to="creation.project",
                )),
                ("promoted_pack", models.ForeignKey(
                    blank=True, null=True, on_delete=models.deletion.SET_NULL,
                    related_name="promoted_from", to="workflow.fusionpipelinepack",
                )),
                ("source_template", models.ForeignKey(
                    blank=True, null=True, on_delete=models.deletion.SET_NULL,
                    related_name="promotions", to="workflow.fusionpipelinepack",
                )),
                ("reviewer", models.ForeignKey(
                    blank=True, null=True, on_delete=models.deletion.SET_NULL,
                    related_name="reviewed_promotions", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"db_table": "ops_template_promotion", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="templatepromotion",
            index=models.Index(fields=["status", "-created_at"], name="ops_tp_idx_status_created"),
        ),
        migrations.AddIndex(
            model_name="templatepromotion",
            index=models.Index(fields=["category", "status"], name="ops_tp_idx_cat_status"),
        ),
        migrations.CreateModel(
            name="TemplatePromotionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=32)),
                ("operator", models.CharField(blank=True, default="", max_length=64)),
                ("from_status", models.CharField(blank=True, default="", max_length=32)),
                ("to_status", models.CharField(blank=True, default="", max_length=32)),
                ("note", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("promotion", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="logs", to="operations.templatepromotion",
                )),
            ],
            options={"db_table": "ops_template_promotion_log", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="templatepromotionlog",
            index=models.Index(fields=["promotion", "-created_at"], name="ops_tpl_idx_prom_created"),
        ),
    ]
