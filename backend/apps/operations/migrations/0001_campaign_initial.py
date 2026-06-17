"""Campaign 模块初始迁移。"""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Campaign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(help_text="活动唯一标识", max_length=64, unique=True)),
                ("name", models.CharField(max_length=128)),
                ("campaign_type", models.CharField(
                    choices=[("new_user", "拉新活动"), ("retention", "留存活动"),
                             ("conversion", "付费转化"), ("brand", "品牌活动"),
                             ("limited", "限时活动"), ("internal", "内部活动")],
                    default="limited", max_length=32,
                )),
                ("status", models.CharField(
                    choices=[("draft", "草稿"), ("scheduled", "待生效"),
                             ("running", "进行中"), ("paused", "已暂停"),
                             ("ended", "已结束"), ("archived", "已归档")],
                    default="draft", max_length=16,
                )),
                ("start_at", models.DateTimeField()),
                ("end_at", models.DateTimeField()),
                ("description", models.TextField(blank=True, default="")),
                ("rules", models.JSONField(default=dict)),
                ("target_user_filter", models.JSONField(default=dict)),
                ("max_claim_per_user", models.PositiveIntegerField(default=1)),
                ("total_quota", models.PositiveIntegerField(default=0)),
                ("claimed_count", models.PositiveIntegerField(default=0)),
                ("created_by", models.CharField(blank=True, default="", max_length=64)),
                ("operator", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "ops_campaign"},
        ),
        migrations.AddIndex(
            model_name="campaign",
            index=models.Index(fields=["status", "-start_at"], name="ops_campaign_idx_status_start"),
        ),
        migrations.AddIndex(
            model_name="campaign",
            index=models.Index(fields=["campaign_type", "status"], name="ops_campaign_idx_type_status"),
        ),
        migrations.CreateModel(
            name="CouponTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128)),
                ("coupon_type", models.CharField(
                    choices=[("coin", "创作币"), ("token", "Token"),
                             ("discount", "折扣"), ("trial", "会员试用"),
                             ("feature", "权益赠送"), ("physical", "实物（占位）")],
                    max_length=24,
                )),
                ("value", models.DecimalField(decimal_places=2, max_digits=12)),
                ("min_spend", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("valid_days", models.PositiveIntegerField(default=30)),
                ("total_quota", models.PositiveIntegerField(default=0)),
                ("issued_count", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(
                    choices=[("active", "可领取"), ("paused", "暂停发放"),
                             ("exhausted", "已发完"), ("expired", "已过期")],
                    default="active", max_length=16,
                )),
                ("scope", models.JSONField(default=dict)),
                ("extra", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("campaign", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.CASCADE,
                    related_name="coupon_templates",
                    to="operations.campaign",
                )),
            ],
            options={"db_table": "ops_coupon_template"},
        ),
        migrations.AddIndex(
            model_name="coupontemplate",
            index=models.Index(fields=["status", "coupon_type"], name="ops_ctpl_idx_status_type"),
        ),
        migrations.CreateModel(
            name="UserCoupon",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(help_text="卡券实例编码", max_length=64, unique=True)),
                ("status", models.CharField(
                    choices=[("unused", "未使用"), ("used", "已使用"),
                             ("expired", "已过期"), ("revoked", "已回收")],
                    default="unused", max_length=16,
                )),
                ("value_snapshot", models.DecimalField(decimal_places=2, max_digits=12)),
                ("min_spend_snapshot", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("valid_from", models.DateTimeField()),
                ("valid_to", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("claim_source", models.CharField(default="campaign", max_length=64)),
                ("redemption_code", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("campaign", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.SET_NULL,
                    related_name="user_coupons",
                    to="operations.campaign",
                )),
                ("template", models.ForeignKey(
                    on_delete=models.deletion.PROTECT,
                    related_name="user_coupons",
                    to="operations.coupontemplate",
                )),
                ("user", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="user_coupons",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"db_table": "ops_user_coupon"},
        ),
        migrations.AddIndex(
            model_name="usercoupon",
            index=models.Index(fields=["user", "status"], name="ops_uc_idx_user_status"),
        ),
        migrations.AddIndex(
            model_name="usercoupon",
            index=models.Index(fields=["valid_to"], name="ops_uc_idx_valid_to"),
        ),
        migrations.CreateModel(
            name="RedemptionCodeBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128)),
                ("code_length", models.PositiveIntegerField(default=12)),
                ("total_count", models.PositiveIntegerField()),
                ("issued_count", models.PositiveIntegerField(default=0)),
                ("claimed_count", models.PositiveIntegerField(default=0)),
                ("prefix", models.CharField(blank=True, default="", max_length=8)),
                ("note", models.TextField(blank=True, default="")),
                ("operator", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("campaign", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.SET_NULL,
                    related_name="code_batches",
                    to="operations.campaign",
                )),
                ("template", models.ForeignKey(
                    on_delete=models.deletion.PROTECT,
                    related_name="code_batches",
                    to="operations.coupontemplate",
                )),
            ],
            options={"db_table": "ops_redemption_batch"},
        ),
        migrations.AddIndex(
            model_name="redemptioncodebatch",
            index=models.Index(fields=["-created_at"], name="ops_rcb_idx_created"),
        ),
        migrations.CreateModel(
            name="RedemptionCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=32, unique=True)),
                ("status", models.CharField(
                    choices=[("unclaimed", "未领取"), ("claimed", "已领取"),
                             ("expired", "已过期"), ("disabled", "已作废")],
                    default="unclaimed", max_length=16,
                )),
                ("claimed_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("batch", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="codes",
                    to="operations.redemptioncodebatch",
                )),
                ("user", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.SET_NULL,
                    related_name="claimed_redemption_codes",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"db_table": "ops_redemption_code"},
        ),
        migrations.AddIndex(
            model_name="redemptioncode",
            index=models.Index(fields=["batch", "status"], name="ops_rc_idx_batch_status"),
        ),
        migrations.AddIndex(
            model_name="redemptioncode",
            index=models.Index(fields=["status", "claimed_at"], name="ops_rc_idx_status_claimed"),
        ),
        migrations.CreateModel(
            name="CouponClaimLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("claim_source", models.CharField(max_length=64)),
                ("result", models.CharField(help_text="success/duplicate/exhausted/expired/blocked", max_length=16)),
                ("reason", models.CharField(blank=True, default="", max_length=255)),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("campaign", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.SET_NULL,
                    to="operations.campaign",
                )),
                ("template", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.SET_NULL,
                    to="operations.coupontemplate",
                )),
                ("user", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.CASCADE,
                    related_name="coupon_claim_logs",
                    to=settings.AUTH_USER_MODEL,
                )),
                ("user_coupon", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.deletion.SET_NULL,
                    to="operations.usercoupon",
                )),
            ],
            options={"db_table": "ops_coupon_claim_log"},
        ),
        migrations.AddIndex(
            model_name="couponclaimlog",
            index=models.Index(fields=["user", "-created_at"], name="ops_ccl_idx_user_created"),
        ),
        migrations.AddIndex(
            model_name="couponclaimlog",
            index=models.Index(fields=["result", "-created_at"], name="ops_ccl_idx_result_created"),
        ),
    ]
