# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Deprecated: external Fusion runtime checks were removed."

    def handle(self, *args, **options):
        raise CommandError(
            "fusion_check has been removed. ScriptForge now uses DB-only assets; "
            "run absorb_external_assets once if migration is needed."
        )
