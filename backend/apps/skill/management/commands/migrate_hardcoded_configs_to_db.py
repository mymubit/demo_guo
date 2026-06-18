# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Deprecated: external asset migration completed."

    def handle(self, *args, **options):
        raise CommandError(
            "migrate_hardcoded_configs_to_db was removed. External asset migration is complete; "
            "use seed_independent_agents or import_agent_assets if needed."
        )
