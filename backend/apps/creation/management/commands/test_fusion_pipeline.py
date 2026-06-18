# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Deprecated: external Fusion pipeline smoke test was removed."

    def handle(self, *args, **options):
        raise CommandError(
            "test_fusion_pipeline has been removed. The main chain now runs through "
            "ScriptForge's 5-step runtime and explicit SkillInvoker post agents."
        )
