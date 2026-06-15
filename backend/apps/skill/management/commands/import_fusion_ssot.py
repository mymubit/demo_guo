# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from apps.workflow.pipeline_store import FusionPipelineDbService


class Command(BaseCommand):
    help = "从 FUSION_SKILL_ROOT 导入主链与 Schema 到数据库（Phase C）"

    def add_arguments(self, parser):
        parser.add_argument("--root", type=str, default="", help="技能包根目录，默认 FUSION_SKILL_ROOT")
        parser.add_argument(
            "--no-activate",
            action="store_true",
            help="导入后不设为 active",
        )

    def handle(self, *args, **options):
        root = options.get("root") or None
        activate = not options.get("no_activate")
        pack_id = FusionPipelineDbService.import_from_disk(activate=activate, root=root)
        meta = FusionPipelineDbService.meta_payload()
        self.stdout.write(
            self.style.SUCCESS(
                f"已导入配置包 {pack_id}，config_source={meta.get('config_source')} "
                f"version={meta.get('db_version')} nodes={meta.get('node_count')}"
            )
        )
