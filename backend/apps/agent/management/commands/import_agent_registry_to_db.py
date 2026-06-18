# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Deprecated: agent registry is seeded by ScriptForge defaults."

    def handle(self, *args, **options):
        raise CommandError(
            "import_agent_registry_to_db was removed. Use AgentDefinitionService.ensure_defaults() "
            "and seed_independent_agents."
        )
