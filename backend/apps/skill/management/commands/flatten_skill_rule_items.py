# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from apps.skill.skills.rule_item_service import SkillRuleItemService


class Command(BaseCommand):
    help = "从 SkillRuleConfig 拆分 SkillRuleItem（skill-agent/11 §4.4）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="归档现有 active Item 后重建",
        )
        parser.add_argument(
            "--as-draft",
            action="store_true",
            default=True,
            help="新建条目为 draft（默认）",
        )

    def handle(self, *args, **options):
        overwrite = bool(options.get("overwrite"))
        as_draft = bool(options.get("as_draft", True))
        counts = SkillRuleItemService.flatten_from_configs(overwrite=overwrite, as_draft=as_draft)
        self.stdout.write(
            self.style.SUCCESS(
                f"flatten 完成: created={counts.get('created')} skipped={counts.get('skipped')} archived={counts.get('archived')}"
            )
        )
