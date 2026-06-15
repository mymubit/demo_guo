# -*- coding: utf-8 -*-
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0002_rechargepackage"),
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="coins_granted",
            field=models.PositiveIntegerField(
                default=0,
                help_text="充值订单支付成功后发放的创作币",
                verbose_name="到账币数",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="order_type",
            field=models.CharField(
                choices=[("membership", "会员购买"), ("recharge", "充值创作币")],
                default="membership",
                max_length=16,
                verbose_name="订单类型",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="recharge_package",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders",
                to="billing.rechargepackage",
                verbose_name="充值档位",
            ),
        ),
    ]
