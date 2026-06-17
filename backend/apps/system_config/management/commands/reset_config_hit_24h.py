# -*- coding: utf-8 -*-
"""【运营 M3】重置 SystemConfigItem.hit_24h 字段。

建议每日 0 点执行一次（cron / dj_queue / supervisor 都可）。
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.system_config.models import SystemConfigItem


class Command(BaseCommand):
    help = "重置 SystemConfigItem.hit_24h 字段为 0（用于每日 0 点的滚动统计）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只统计数量，不实际更新",
        )

    def handle(self, *args, **options):
        qs = SystemConfigItem.objects.filter(deleted_at__isnull=True)
        total = qs.filter(hit_24h__gt=0).count()
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING(
                f"[DRY-RUN] 将重置 {total} 条配置的 hit_24h 字段"
            ))
            return
        updated = qs.update(hit_24h=0, last_hit_at=timezone.now())
        self.stdout.write(self.style.SUCCESS(
            f"已重置 {updated} 条配置的 hit_24h 字段"
        ))
