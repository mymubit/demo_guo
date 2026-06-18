# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Deprecated: use absorb_external_assets."

    def handle(self, *args, **options):
        raise CommandError("import_skill_rules_to_db was removed. Use absorb_external_assets for the one-time asset migration.")
