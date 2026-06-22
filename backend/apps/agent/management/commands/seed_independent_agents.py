# -*- coding: utf-8 -*-
"""
种入 drama.* Agent 定义的兼容命令。

此命令现在等价于 seed_drama_skills，保留是为了向后兼容。
推荐直接使用：python manage.py seed_drama_skills
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "种入 drama.* 36个角色（等价于 seed_drama_skills，请优先使用该命令）。"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "此命令已更新，现在等价于 seed_drama_skills。"
                "推荐直接使用：python manage.py seed_drama_skills"
            )
        )
        from django.core.management import call_command
        call_command("seed_drama_skills", *args, **options)
