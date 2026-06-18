# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from apps.workflow.pipeline_store import FusionPipelineDbService


class Command(BaseCommand):
    help = "Deprecated. DB-only default pack."

    def add_arguments(self, parser):
        return None

    def handle(self, *args, **options):
        pack = FusionPipelineDbService.ensure_builtin_default_pack()
        meta = FusionPipelineDbService.meta_payload()
        self.stdout.write(
            self.style.SUCCESS(
                f"DB-only default pack ensured: {pack.id}; config_source={meta.get('config_source')} "
                f"version={meta.get('db_version')} nodes={meta.get('node_count')}"
            )
        )
