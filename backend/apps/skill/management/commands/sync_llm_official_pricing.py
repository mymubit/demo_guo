# -*- coding: utf-8 -*-
"""将种子中的官方 Token 单价强制写入大模型目录，并重算历史 LLM 费用估算。"""
from django.core.management.base import BaseCommand

from apps.skill.llm.model_catalog import LlmCatalogService
from apps.skill.llm.usage_log import LlmUsageService


class Command(BaseCommand):
    help = "同步大模型目录官方单价（元/百万 Token），并重算 LlmUsageLog 估算费用"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-recalculate",
            action="store_true",
            help="仅更新目录单价，不重算历史 usage 日志",
        )
        parser.add_argument(
            "--preset",
            action="append",
            dest="presets",
            metavar="PRESET_KEY",
            help="仅同步指定 preset_key，可重复传入",
        )

    def handle(self, *args, **options):
        self.stdout.write("同步大模型官方单价…")
        LlmCatalogService.ensure_seed_catalog()
        updated = LlmCatalogService.sync_official_pricing(preset_keys=options.get("presets"))
        self.stdout.write(self.style.SUCCESS(f"目录单价已更新 {updated} 条"))

        if options.get("skip_recalculate"):
            return

        recalculated = LlmUsageService.recalculate_estimated_costs(all_logs=True)
        self.stdout.write(self.style.SUCCESS(f"历史 LLM 费用重算 {recalculated} 条"))
