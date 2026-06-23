# -*- coding: utf-8 -*-
# Generated migration: SystemConfigItem 命中率统计字段（运营 M3）
# 新增 hit_count / hit_24h / last_hit_at

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system_config', '0002_sensitiveword'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemconfigitem',
            name='hit_count',
            field=models.PositiveBigIntegerField(
                default=0,
                help_text='C 端/后台读取该配置项的累计次数（含缓存命中与未命中）',
                verbose_name='总命中次数',
            ),
        ),
        migrations.AddField(
            model_name='systemconfigitem',
            name='hit_24h',
            field=models.PositiveIntegerField(
                default=0,
                help_text='过去 24h 的命中次数（每日零点重置，或在 track_hit 时自维护）',
                verbose_name='24h 命中次数',
            ),
        ),
        migrations.AddField(
            model_name='systemconfigitem',
            name='last_hit_at',
            field=models.DateTimeField(
                blank=True, db_index=True, null=True,
                verbose_name='最近命中时间',
            ),
        ),
    ]
