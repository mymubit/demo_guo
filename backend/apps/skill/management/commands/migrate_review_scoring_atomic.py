# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from apps.skill.services.review_scoring_atomic import seed_presets_from_defaults


class Command(BaseCommand):
    help = "从 review_scoring_defaults 种子 ReviewScoringPreset 三表（skill-agent/13 §4）"

    def add_arguments(self, parser):
        parser.add_argument("--overwrite", action="store_true", help="重建维度/等级行")

    def handle(self, *args, **options):
        created = seed_presets_from_defaults(overwrite=bool(options.get("overwrite")))
        self.stdout.write(self.style.SUCCESS(f"ReviewScoring 预设种子完成: created={created}"))
