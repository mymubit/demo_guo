# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from apps.billing.models import ActionPricing, SiteCoinSettings
from apps.billing.ai_field_prompt_service import AiFieldPromptService

DEFAULT_PRICING = [
    ("creation.submit", "发起创作", 5, 10, False),
    ("drama.agent.topic-planner", "Drama·选题策划", 3, 20, False),
    ("drama.agent.world-architect", "Drama·世界观", 4, 30, False),
    ("drama.agent.character-designer", "Drama·角色设计", 5, 40, False),
    ("drama.agent.plot-architect", "Drama·剧情架构", 8, 50, False),
    ("drama.agent.script-writer", "Drama·剧本创作", 15, 60, False),
    ("drama.agent.script-reviewer", "Drama·剧本审查", 5, 70, False),
    ("drama.agent.quality-reporter", "Drama·质量报告", 6, 80, False),
    ("drama.agent.compliance-guard", "Drama·合规审查", 6, 90, False),
    ("ai.generate.core_idea", "AI·核心创意", 20, 100, False),
    ("ai.generate.audience", "AI·目标受众", 10, 110, False),
    ("ai.generate.reference_work", "AI·参考作品", 10, 120, False),
    ("ai.generate.worldview", "AI·世界观", 15, 130, False),
    ("ai.generate.inspiration_plan", "AI·灵感策划", 30, 140, True),
    ("ai.generate.pull_sheet", "拉片分析", 50, 150, True),
]


class Command(BaseCommand):
    help = "初始化币种定价与站点设置"

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
        AiFieldPromptService.seed_defaults()
        self.stdout.write(self.style.SUCCESS("计费数据已初始化"))
