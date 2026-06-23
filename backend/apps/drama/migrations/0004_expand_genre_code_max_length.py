# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drama", "0003_dramagenerationplan_dramaepisodeplan"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dramaproject",
            name="genre_code",
            field=models.CharField(
                default="family-revenge",
                max_length=64,
                verbose_name="题材代码",
            ),
        ),
        migrations.AlterField(
            model_name="dramaproject",
            name="track_mode",
            field=models.CharField(
                choices=[
                    ("fast", "快速通道（8核心角色）"),
                    ("expert", "专家通道（12角色）"),
                ],
                default="fast",
                max_length=16,
                verbose_name="创作模式",
            ),
        ),
    ]
