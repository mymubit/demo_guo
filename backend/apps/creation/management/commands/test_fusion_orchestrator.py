# -*- coding: utf-8 -*-
"""本地冒烟：融合编排器节点 1–5（需 LLM + sub-brief/gate CLI）。"""
import json
import uuid

from django.core.management.base import BaseCommand, CommandError

from apps.creation.fusion.fusion_orchestrator import FusionOrchestrator
from apps.creation.models import Project
from apps.skill.llm.chat import LlmService


class Command(BaseCommand):
    help = "LLM 跑通节点1–5 + 逐集 gate（内存 Project，不写库；需配置 LLM）"

    def add_arguments(self, parser):
        parser.add_argument("--episodes", type=int, default=30)
        parser.add_argument("--theme", default="family-revenge")

    def handle(self, *args, **options):
        if not LlmService.is_enabled():
            raise CommandError(
                "LLM 未启用：请设置 FUSION_LLM_ENABLED=true 并配置 SkillConfig llm.enabled / api_key / base_url"
            )

        project = Project(
            id=uuid.uuid4(),
            theme=options["theme"],
            core_idea="女主隐忍五年后带合同对峙豪门，身份反转打脸全场。",
            episode_count=options["episodes"],
            format_variant="B",
            target_platform="douyin",
            budget_level="medium",
            creation_entry="from-scratch",
            episode_duration_minutes=2.0,
            title="冒烟测试项目",
        )
        orch = FusionOrchestrator(project, dry_run=True)
        result = orch.run()

        artifacts = result.get("artifacts") or {}
        scripts = artifacts.get("episode_scripts") or {}
        eps = scripts.get("episodes") or []
        gate_pass = sum(1 for e in eps if (e.get("gateLog") or {}).get("passed"))

        summary = {
            "status": result.get("status"),
            "errors": result.get("errors"),
            "artifact_keys": list(artifacts.keys()),
            "episodes": len(eps),
            "gate_passed": gate_pass,
            "brief_has_trend": bool((artifacts.get("project_brief") or {}).get("trendFormula")),
            "llm_mode": True,
        }
        self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2))
        if result.get("status") != "completed":
            raise CommandError("编排未成功完成")
