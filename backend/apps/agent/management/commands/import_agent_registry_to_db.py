# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Deprecated: agent registry is seeded by ScriptForge defaults."

    def handle(self, *args, **options):
        raise CommandError("import_agent_registry_to_db was removed. Use ScriptForge DB defaults and absorb_external_assets.")
