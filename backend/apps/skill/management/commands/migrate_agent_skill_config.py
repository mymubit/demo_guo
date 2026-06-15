# -*- coding: utf-8 -*-
"""将流水线节点遗留技能配置迁入 Agent Registry。"""
from django.core.management.base import BaseCommand

from apps.agent.routes import AgentLlmRouteService
from apps.agent.registry import AgentRegistryConfigService


class Command(BaseCommand):
    help = "迁移 FusionPipelineNode 技能字段到 Agent Registry 与 Agent LLM 路由"

    def handle(self, *args, **options):
        AgentRegistryConfigService.ensure_defaults()
        seeded = AgentLlmRouteService.seed_defaults()
        migrated = AgentRegistryConfigService.migrate_pipeline_skill_config()
        self.stdout.write(
            self.style.SUCCESS(
                f"完成：seed 路由 {seeded} 条，迁移 Agent 技能配置 {migrated} 个"
            )
        )
