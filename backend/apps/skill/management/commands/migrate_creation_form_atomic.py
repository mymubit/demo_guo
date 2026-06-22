# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from apps.skill.services.creation_form_atomic_sync import migrate_from_overrides


class Command(BaseCommand):
    help = "将 CreationFormOverrideConfig JSON 拆分为原子子表（skill-agent/13 §3）"

    def add_arguments(self, parser):
        parser.add_argument("--overwrite", action="store_true", help="清空后重建")
        parser.add_argument("--config-key", type=str, default="default")

    def handle(self, *args, **options):
        counts = migrate_from_overrides(
            config_key=str(options.get("config_key") or "default"),
            overwrite=bool(options.get("overwrite")),
        )
        self.stdout.write(self.style.SUCCESS(f"creation form atomic 迁移完成: {counts}"))
