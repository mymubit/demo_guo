# -*- coding: utf-8 -*-
import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RechargePackage",
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
                ("name", models.CharField(max_length=64, verbose_name="档位名称")),
                (
                    "price_yuan",
                    models.DecimalField(
                        decimal_places=2, max_digits=10, verbose_name="价格（元）"
                    ),
                ),
                (
                    "base_coins",
                    models.PositiveIntegerField(default=0, verbose_name="基础币数"),
                ),
                (
                    "bonus_coins",
                    models.PositiveIntegerField(default=0, verbose_name="赠送币数"),
                ),
                (
                    "original_price_yuan",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="可选，用于展示优惠",
                        max_digits=10,
                        null=True,
                        verbose_name="划线原价（元）",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="启用")),
                (
                    "sort_order",
                    models.PositiveSmallIntegerField(default=0, verbose_name="排序"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "充值档位",
                "verbose_name_plural": "充值档位",
                "db_table": "billing_recharge_package",
                "ordering": ["sort_order", "price_yuan"],
            },
        ),
    ]
