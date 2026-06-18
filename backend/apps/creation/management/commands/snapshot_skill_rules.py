# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Deprecated: disk skill-rule snapshots were removed."

    def handle(self, *args, **options):
        raise CommandError(
            "snapshot_skill_rules has been removed. Skill rules are DB-only in ScriptForge; "
            "use the admin DB tooling. One-time external asset migration is already complete."
        )
