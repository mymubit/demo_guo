# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from apps.billing.models import ActionPricing, SiteCoinSettings
from apps.workflow.services.pipeline_service import WorkflowPipelineService
from apps.billing.ai_field_prompt_service import AiFieldPromptService

DEFAULT_PRICING = [
    ("creation.submit", "发起创作", 5, 10, False),
    ("pipeline.node.1", "1. 立项策划 (BriefAgent)", 5, 20, False),
    ("pipeline.node.2", "2. 结构与世界观 (WorldAgent)", 10, 30, False),
    ("pipeline.node.3", "3. 角色设计 (CharacterAgent)", 10, 40, False),
    ("pipeline.node.4", "4. 大纲与创作规划 (OutlineAgent)", 15, 50, False),
    ("pipeline.node.5", "5. 剧集剧本 (ScriptAgent)", 30, 60, False),
    ("pipeline.node.6", "6. 质检审查 (ReviewAgent)", 10, 70, False),
    ("pipeline.node.7", "7. 深度评估 (ScoreAgent)", 10, 80, False),
    ("pipeline.regenerate", "重跑 Agent 步骤", 0, 90, False),
    ("ai.generate.core_idea", "AI·核心创意", 20, 100, False),
    ("ai.generate.audience", "AI·目标受众", 10, 110, False),
    ("ai.generate.reference_work", "AI·参考作品", 10, 120, False),
    ("ai.generate.worldview", "AI·世界观", 15, 130, False),
    ("ai.generate.inspiration_plan", "AI·灵感策划", 30, 140, True),
    ("ai.generate.pull_sheet", "拉片分析", 50, 150, True),
]


class Command(BaseCommand):
    help = "初始化币种定价、站点设置、流程节点编排"

    def handle(self, *args, **options):
        SiteCoinSettings.load()
        for key, name, cost, order, member_only in DEFAULT_PRICING:
            ActionPricing.objects.update_or_create(
                action_key=key,
                defaults={
                    "display_name": name,
                    "coin_cost": cost,
                    "is_active": True,
                    "sort_order": order,
                    "member_only": member_only,
                },
            )
        WorkflowPipelineService.ensure_defaults()
        AiFieldPromptService.seed_defaults()
        self.stdout.write(self.style.SUCCESS("计费与流程编排数据已初始化"))
