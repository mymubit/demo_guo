# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0002_rechargepackage"),
    ]

    operations = [
        migrations.AddField(
            model_name="actionpricing",
            name="member_only",
            field=models.BooleanField(
                default=False,
                help_text="开启后须有效会员才可执行该动作",
                verbose_name="仅会员可用",
            ),
        ),
    ]
