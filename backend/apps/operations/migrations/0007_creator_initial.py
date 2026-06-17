"""创作者激励初始化。"""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0006_ugc_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CreatorLevel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(help_text="L1 / L2 / L3 ...", max_length=32, unique=True)),
                ("name", models.CharField(help_text="见习创作者 / 进阶 / 大神 ...", max_length=64)),
                ("min_points", models.PositiveIntegerField(help_text="累计积分门槛")),
                ("max_points", models.PositiveIntegerField(default=0, help_text="累计积分上限 (0 = 无上限)")),
                ("badge_icon", models.CharField(blank=True, default="", max_length=256)),
                ("benefits", models.JSONField(default=list, help_text="权益说明")),
                ("order", models.IntegerField(default=0, help_text="排序权重")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "ops_creator_level",
                "ordering": ["order", "min_points"],
            },
        ),
        migrations.CreateModel(
            name="CreatorProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("total_points", models.BigIntegerField(default=0, help_text="累计获得积分（仅入账方向）")),
                ("available_points", models.BigIntegerField(default=0, help_text="可用积分（可用于兑换）")),
                ("used_points", models.BigIntegerField(default=0, help_text="已消耗积分")),
                ("project_count", models.PositiveIntegerField(default=0)),
                ("template_count", models.PositiveIntegerField(default=0)),
                ("is_certified", models.BooleanField(default=False, help_text="官方认证")),
                ("certified_at", models.DateTimeField(blank=True, null=True)),
                ("bio", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("level", models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="members", to="operations.creatorlevel")),
            ],
            options={
                "db_table": "ops_creator_profile",
            },
        ),
        migrations.CreateModel(
            name="PointsAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("balance", models.BigIntegerField(default=0, help_text="当前可用积分")),
                ("total_earned", models.BigIntegerField(default=0)),
                ("total_spent", models.BigIntegerField(default=0)),
                ("frozen", models.BigIntegerField(default=0, help_text="冻结积分（风控 / 争议中）")),
                ("last_change_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "ops_points_account",
            },
        ),
        migrations.CreateModel(
            name="PointsTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("delta", models.BigIntegerField(help_text="正数入账 / 负数消耗")),
                ("reason", models.CharField(choices=[("project_completed", "完成项目"), ("script_adopted", "剧本被采纳"), ("template_used", "模板被使用"), ("template_rated", "模板被评分"), ("daily_login", "每日登录"), ("share", "分享"), ("exchange", "兑换消耗"), ("admin_adjust", "运营调整")], max_length=32)),
                ("ref_type", models.CharField(blank=True, default="", help_text="关联对象类型：project / template / ticket ...", max_length=32)),
                ("ref_id", models.CharField(blank=True, default="", max_length=64)),
                ("note", models.CharField(blank=True, default="", max_length=255)),
                ("operator", models.CharField(blank=True, default="", help_text="admin_adjust 时记录运营账号", max_length=64)),
                ("balance_after", models.BigIntegerField(default=0, help_text="操作后余额")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "ops_points_transaction",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Badge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=64)),
                ("description", models.TextField(blank=True, default="")),
                ("icon_url", models.CharField(blank=True, default="", max_length=512)),
                ("trigger_event", models.CharField(blank=True, default="", max_length=64)),
                ("trigger_threshold", models.PositiveIntegerField(default=0)),
                ("rarity", models.CharField(default="common", help_text="common / rare / epic / legend", max_length=16)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "ops_badge",
                "ordering": ["rarity", "code"],
            },
        ),
        migrations.CreateModel(
            name="CreatorAchievement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("progress", models.PositiveIntegerField(default=100, help_text="达成进度 0-100")),
                ("unlocked_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=models.CASCADE, related_name="achievements", to=settings.AUTH_USER_MODEL)),
                ("badge", models.ForeignKey(on_delete=models.CASCADE, related_name="achievements", to="operations.badge")),
            ],
            options={
                "db_table": "ops_creator_achievement",
            },
        ),
        migrations.AddIndex(
            model_name="creatorprofile",
            index=models.Index(fields=["-total_points"], name="ops_creator_total_p_3a8b21_idx"),
        ),
        migrations.AddIndex(
            model_name="creatorprofile",
            index=models.Index(fields=["level", "-total_points"], name="ops_creator_level_4c1f77_idx"),
        ),
        migrations.AddIndex(
            model_name="pointstransaction",
            index=models.Index(fields=["user", "-created_at"], name="ops_points_user_id_8d3a91_idx"),
        ),
        migrations.AddIndex(
            model_name="pointstransaction",
            index=models.Index(fields=["reason", "-created_at"], name="ops_points_reason_4f9c2e_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="creatorachievement",
            unique_together={("user", "badge")},
        ),
        migrations.AddIndex(
            model_name="creatorachievement",
            index=models.Index(fields=["user", "-unlocked_at"], name="ops_creator_user_id_3b8c44_idx"),
        ),
    ]
