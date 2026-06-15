# -*- coding: utf-8 -*-
from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("membership", "0003_membershipfeaturematrixitem"),
    ]

    operations = [
        migrations.AddField(
            model_name="membershipplan",
            name="original_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="可选，用于展示划线价与折扣计算",
                max_digits=10,
                null=True,
                verbose_name="划线原价(元)",
            ),
        ),
        migrations.AddField(
            model_name="membershipplan",
            name="discount_percent",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("100"),
                help_text="100 表示无折扣；有划线原价时按 原价×折扣% 计算实付",
                max_digits=5,
                verbose_name="折扣(%)",
            ),
        ),
    ]
