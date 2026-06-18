# -*- coding: utf-8 -*-
"""【运营 M2】批量弃用项目扫描。

将 N 天未编辑且未完成的项目标记为弃用（abandoned_at）。
用于一人运营的日常 cron（建议每日凌晨执行）。
"""
from django.core.management.base import BaseCommand

from apps.creation.services.content_quality import detect_and_mark_abandoned


class Command(BaseCommand):
    help = "扫描 N 天未编辑且未完成的创作项目，标记为弃用（用于运营 Dashboard 漏斗）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="超过 N 天未编辑即视为弃用（默认 7）",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=500,
            help="单次最大处理数（避免锁表，默认 500）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只统计数量，不实际更新",
        )

    def handle(self, *args, **options):
        days = options["days"]
        limit = options["limit"]
        dry_run = options["dry_run"]
        if dry_run:
            from django.utils import timezone
            from datetime import timedelta
            from django.db.models import Q
            from apps.creation.models import Project

            threshold_dt = timezone.now() - timedelta(days=days)
            cnt = Project.objects.filter(
                abandoned_at__isnull=True,
            ).exclude(fusion_status=Project.FUSION_READY).filter(
                Q(last_edited_at__isnull=True, created_at__lt=threshold_dt)
                | Q(last_edited_at__lt=threshold_dt)
            ).count()
            self.stdout.write(self.style.WARNING(
                f"[DRY-RUN] 将标记 {cnt} 个项目为弃用（>={days} 天未编辑且未完成）"
            ))
            return

        count = detect_and_mark_abandoned(days=days, limit=limit)
        self.stdout.write(self.style.SUCCESS(
            f"已弃用 {count} 个创作项目（>={days} 天未编辑且未完成）"
        ))
