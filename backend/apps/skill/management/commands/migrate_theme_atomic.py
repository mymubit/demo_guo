# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from apps.skill.models import ThemeTemplate
from apps.skill.services.theme_atomic_sync import sync_params_from_atomic_tables


class Command(BaseCommand):
    help = "从 Theme 原子子表写回 params cache（skill-agent/13 Phase C）"

    def add_arguments(self, parser):
        parser.add_argument("--theme-code", type=str, default="", help="仅同步指定题材")
        parser.add_argument("--import-params", action="store_true", help="从 params JSON 导入子表")
        parser.add_argument("--overwrite", action="store_true", help="导入前清空子表")

    def handle(self, *args, **options):
        code = (options.get("theme_code") or "").strip()
        import_params = bool(options.get("import_params"))
        qs = ThemeTemplate.objects.all()
        if code:
            qs = qs.filter(theme_code=code)
        count = 0
        for theme in qs:
            if import_params:
                from apps.skill.services.theme_atomic_sync import import_from_params

                import_from_params(theme, overwrite=bool(options.get("overwrite")))
            sync_params_from_atomic_tables(theme)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"已同步 {count} 个题材 params cache"))
