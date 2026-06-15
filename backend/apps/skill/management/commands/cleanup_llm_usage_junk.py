# -*- coding: utf-8 -*-
"""清理 LlmUsageLog 中单元测试/调试占位记录（如 t/m、test/test）。"""
from django.core.management.base import BaseCommand

from apps.skill.llm.usage_log import LlmUsageService


class Command(BaseCommand):
    help = "删除 LlmUsageLog 中的测试占位用量（t/m、test/test、ep-test 等）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅统计将删除条数，不实际删除",
        )

    def handle(self, *args, **options):
        dry_run = bool(options.get("dry_run"))
        if dry_run:
            count = LlmUsageService.cleanup_junk_logs(dry_run=True)
            self.stdout.write(self.style.WARNING(f"将删除 {count} 条占位用量日志（dry-run）"))
            return

        deleted = LlmUsageService.cleanup_junk_logs()
        self.stdout.write(self.style.SUCCESS(f"已删除 {deleted} 条占位用量日志"))
