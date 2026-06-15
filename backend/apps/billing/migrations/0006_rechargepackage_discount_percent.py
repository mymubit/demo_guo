# -*- coding: utf-8 -*-
from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0005_aifieldprompt_llm_provider"),
    ]

    operations = [
        migrations.AddField(
            model_name="rechargepackage",
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
