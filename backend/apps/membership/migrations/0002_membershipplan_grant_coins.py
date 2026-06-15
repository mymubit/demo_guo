# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("membership", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="membershipplan",
            name="grant_coins",
            field=models.PositiveIntegerField(
                default=0,
                help_text="开通/续费该套餐时发放的网站币",
                verbose_name="开通赠送币",
            ),
        ),
        migrations.AlterField(
            model_name="membershipplan",
            name="creation_quota",
            field=models.IntegerField(
                default=0,
                help_text="遗留字段；商业站以 grant_coins 为准",
                verbose_name="创作次数配额",
            ),
        ),
    ]
