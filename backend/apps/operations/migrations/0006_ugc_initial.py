"""UGC 模板市场初始化。"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0005_template_promotion_initial"),
        ("workflow", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=128, unique=True)),
                ("name", models.CharField(max_length=128)),
                ("description", models.TextField(blank=True, default="")),
                ("category", models.CharField(blank=True, default="", max_length=64)),
                ("tags", models.JSONField(default=list, help_text="标签：甜宠 / 悬疑 / 高反转 等")),
                ("cover_url", models.CharField(blank=True, default="", max_length=512)),
                ("pack_snapshot", models.JSONField(default=dict, help_text="包快照：nodes / edges / runner_path / skill_id 列表")),
                ("status", models.CharField(choices=[("draft", "草稿"), ("pending", "待审核"), ("published", "已发布"), ("rejected", "已驳回"), ("offline", "已下架")], default="draft", max_length=16)),
                ("review_note", models.TextField(blank=True, default="")),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("downloads_count", models.PositiveIntegerField(default=0)),
                ("uses_count", models.PositiveIntegerField(default=0)),
                ("rating_count", models.PositiveIntegerField(default=0)),
                ("rating_avg", models.DecimalField(decimal_places=2, default=0, max_digits=3)),
                ("collection_count", models.PositiveIntegerField(default=0)),
                ("is_featured", models.BooleanField(default=False, help_text="运营置顶")),
                ("sort_weight", models.IntegerField(default=0, help_text="运营人工排序权重")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "ops_user_template",
                "ordering": ["-is_featured", "-sort_weight", "-published_at"],
            },
        ),
        migrations.CreateModel(
            name="UserTemplateRating",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.PositiveSmallIntegerField(help_text="1-5 星")),
                ("comment", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "ops_user_template_rating",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="UserTemplateCollection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("collection_name", models.CharField(blank=True, default="", help_text="收藏夹名（默认 '默认收藏夹'）", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "ops_user_template_collection",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="usertemplate",
            index=models.Index(fields=["status", "-published_at"], name="ops_user_t_status_5b2884_idx"),
        ),
        migrations.AddIndex(
            model_name="usertemplate",
            index=models.Index(fields=["category", "status"], name="ops_user_t_categor_3a8e4f_idx"),
        ),
        migrations.AddIndex(
            model_name="usertemplate",
            index=models.Index(fields=["author", "status"], name="ops_user_t_author__6f47c2_idx"),
        ),
        migrations.AddIndex(
            model_name="usertemplate",
            index=models.Index(fields=["-downloads_count"], name="ops_user_t_downloa_b6a0d1_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="usertemplaterating",
            unique_together={("template", "user")},
        ),
        migrations.AddIndex(
            model_name="usertemplaterating",
            index=models.Index(fields=["template", "-created_at"], name="ops_user_t_templat_d0c7f3_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="usertemplatecollection",
            unique_together={("template", "user")},
        ),
        migrations.AddIndex(
            model_name="usertemplatecollection",
            index=models.Index(fields=["user", "-created_at"], name="ops_user_t_user_id_4d4e2c_idx"),
        ),
    ]
