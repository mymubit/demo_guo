# -*- coding: utf-8 -*-
import uuid

from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteCoinSettings",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("currency_name", models.CharField(default="创作币", max_length=32, verbose_name="币种名称")),
                ("signup_bonus", models.PositiveIntegerField(default=100, verbose_name="注册赠送")),
                (
                    "default_pipeline_mode",
                    models.CharField(
                        choices=[("auto", "一键生成"), ("step", "分步掌控")],
                        default="step",
                        max_length=8,
                        verbose_name="默认创作模式",
                    ),
                ),
                (
                    "require_membership_for_creation",
                    models.BooleanField(default=True, help_text="开启后须有效会员才可发起创作（仍按币扣费）", verbose_name="创作需有效会员"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "站点币种设置",
                "verbose_name_plural": "站点币种设置",
                "db_table": "billing_site_coin_settings",
            },
        ),
        migrations.CreateModel(
            name="ActionPricing",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("action_key", models.CharField(max_length=64, unique=True, verbose_name="动作键")),
                ("display_name", models.CharField(max_length=100, verbose_name="展示名称")),
                ("coin_cost", models.PositiveIntegerField(default=0, verbose_name="消耗币数")),
                ("is_active", models.BooleanField(default=True, verbose_name="启用")),
                ("sort_order", models.IntegerField(default=0, verbose_name="排序")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "动作定价",
                "verbose_name_plural": "动作定价",
                "db_table": "billing_action_pricing",
                "ordering": ["sort_order", "action_key"],
            },
        ),
        migrations.CreateModel(
            name="PipelineNodeConfig",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("fusion_node_id", models.CharField(max_length=64, unique=True, verbose_name="融合节点ID")),
                ("node_index", models.PositiveSmallIntegerField(unique=True, verbose_name="步骤序号")),
                ("display_name", models.CharField(max_length=100, verbose_name="前台展示名")),
                ("enabled", models.BooleanField(default=True, verbose_name="启用")),
                ("requires_confirm", models.BooleanField(default=True, verbose_name="分步模式需确认")),
                ("coin_cost", models.PositiveIntegerField(default=10, help_text="执行该节点时扣费；0 表示走 ActionPricing 默认键", verbose_name="单步消耗币")),
                ("sort_order", models.PositiveSmallIntegerField(default=0, verbose_name="排序")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "流程节点编排",
                "verbose_name_plural": "流程节点编排",
                "db_table": "billing_pipeline_node_config",
                "ordering": ["sort_order", "node_index"],
            },
        ),
        migrations.CreateModel(
            name="UserWallet",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("balance", models.PositiveIntegerField(default=0, verbose_name="余额")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=models.deletion.CASCADE,
                        related_name="wallet",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "用户钱包",
                "verbose_name_plural": "用户钱包",
                "db_table": "billing_user_wallet",
            },
        ),
        migrations.CreateModel(
            name="CoinLedger",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("delta", models.IntegerField(verbose_name="变动量（负为消耗）")),
                ("balance_after", models.PositiveIntegerField(verbose_name="变动后余额")),
                (
                    "entry_type",
                    models.CharField(
                        choices=[("grant", "发放"), ("spend", "消耗"), ("refund", "退还"), ("adjust", "人工调整")],
                        max_length=16,
                        verbose_name="类型",
                    ),
                ),
                ("action_key", models.CharField(blank=True, default="", max_length=64, verbose_name="动作键")),
                ("reference_id", models.CharField(blank=True, default="", max_length=64, verbose_name="关联ID")),
                ("remark", models.CharField(blank=True, default="", max_length=200, verbose_name="备注")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="coin_ledgers",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "币种流水",
                "verbose_name_plural": "币种流水",
                "db_table": "billing_coin_ledger",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="coinledger",
            index=models.Index(fields=["user", "-created_at"], name="billing_coi_user_id_6a8fbd_idx"),
        ),
        migrations.AddIndex(
            model_name="coinledger",
            index=models.Index(fields=["action_key"], name="billing_coi_action__f8e2a1_idx"),
        ),
    ]
