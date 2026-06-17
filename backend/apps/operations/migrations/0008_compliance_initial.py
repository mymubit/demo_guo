"""合规规则初始化。"""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0007_creator_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SensitiveWord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("word", models.CharField(max_length=128, unique=True)),
                ("category", models.CharField(choices=[("sensitive_word", "敏感词"), ("topic_risk", "题材风险"), ("ip_risk", "IP 侵权"), ("politics", "政治安全"), ("violence", "暴力血腥"), ("adult", "成人内容"), ("other", "其他")], max_length=32)),
                ("level", models.CharField(choices=[("P0", "硬熔断"), ("P1", "提示告警"), ("P2", "仅记录")], max_length=8)),
                ("description", models.CharField(blank=True, default="", max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_by", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "ops_sensitive_word",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="TopicBlacklist",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128, unique=True)),
                ("keywords", models.JSONField(default=list, help_text="关键词列表")),
                ("category", models.CharField(choices=[("sensitive_word", "敏感词"), ("topic_risk", "题材风险"), ("ip_risk", "IP 侵权"), ("politics", "政治安全"), ("violence", "暴力血腥"), ("adult", "成人内容"), ("other", "其他")], default="topic_risk", max_length=32)),
                ("level", models.CharField(choices=[("P0", "硬熔断"), ("P1", "提示告警"), ("P2", "仅记录")], default="P0", max_length=8)),
                ("reason", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
                ("created_by", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "ops_topic_blacklist",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="ComplianceRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128, unique=True)),
                ("description", models.TextField(blank=True, default="")),
                ("category", models.CharField(choices=[("sensitive_word", "敏感词"), ("topic_risk", "题材风险"), ("ip_risk", "IP 侵权"), ("politics", "政治安全"), ("violence", "暴力血腥"), ("adult", "成人内容"), ("other", "其他")], max_length=32)),
                ("level", models.CharField(choices=[("P0", "硬熔断"), ("P1", "提示告警"), ("P2", "仅记录")], max_length=8)),
                ("rule_expr", models.JSONField(default=dict)),
                ("scope", models.CharField(default="all", help_text="title/outline/script/all", max_length=32)),
                ("is_active", models.BooleanField(default=True)),
                ("created_by", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "ops_compliance_rule",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="ViolationLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(choices=[("sensitive_word", "敏感词"), ("topic_risk", "题材风险"), ("ip_risk", "IP 侵权"), ("politics", "政治安全"), ("violence", "暴力血腥"), ("adult", "成人内容"), ("other", "其他")], max_length=32)),
                ("level", models.CharField(choices=[("P0", "硬熔断"), ("P1", "提示告警"), ("P2", "仅记录")], max_length=8)),
                ("source", models.CharField(default="auto", help_text="auto / manual / user_report", max_length=32)),
                ("matched_text", models.TextField(blank=True, default="")),
                ("rule_name", models.CharField(blank=True, default="", max_length=128)),
                ("action_taken", models.CharField(blank=True, default="", help_text="block / warn / record", max_length=64)),
                ("handled", models.BooleanField(default=False)),
                ("handled_by", models.CharField(blank=True, default="", max_length=64)),
                ("handled_at", models.DateTimeField(blank=True, null=True)),
                ("handle_note", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="violation_logs", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="violation_logs", to="creation.project")),
            ],
            options={
                "db_table": "ops_violation_log",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ComplianceRuleVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.CharField(max_length=32, unique=True)),
                ("snapshot", models.JSONField(default=dict, help_text="规则库完整快照")),
                ("note", models.TextField(blank=True, default="")),
                ("published_by", models.CharField(blank=True, default="", max_length=64)),
                ("published_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "ops_compliance_version",
                "ordering": ["-published_at"],
            },
        ),
        migrations.AddIndex(
            model_name="sensitiveword",
            index=models.Index(fields=["is_active", "category"], name="ops_sensit_is_acti_5a3b1f_idx"),
        ),
        migrations.AddIndex(
            model_name="sensitiveword",
            index=models.Index(fields=["level", "is_active"], name="ops_sensit_level_i_8d2c4e_idx"),
        ),
        migrations.AddIndex(
            model_name="topicblacklist",
            index=models.Index(fields=["is_active", "category"], name="ops_topicb_is_acti_3f7e22_idx"),
        ),
        migrations.AddIndex(
            model_name="compliancerule",
            index=models.Index(fields=["is_active", "level"], name="ops_compli_is_acti_9b4d31_idx"),
        ),
        migrations.AddIndex(
            model_name="compliancerule",
            index=models.Index(fields=["category", "is_active"], name="ops_compli_categor_1c2e7a_idx"),
        ),
        migrations.AddIndex(
            model_name="violationlog",
            index=models.Index(fields=["-created_at"], name="ops_violat_created_5a2b88_idx"),
        ),
        migrations.AddIndex(
            model_name="violationlog",
            index=models.Index(fields=["level", "-created_at"], name="ops_violat_level_c_3b1a99_idx"),
        ),
        migrations.AddIndex(
            model_name="violationlog",
            index=models.Index(fields=["handled", "-created_at"], name="ops_violat_handled_4f8c2c_idx"),
        ),
    ]
