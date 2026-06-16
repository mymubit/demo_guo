"""
将硬编码的 _SUB_SKILL_SYSTEM_HINTS 写入 AgentRegistryConfig（DB），
使运营可在管理后台直接修改子技能提示词，无需改代码重新部署。

用法：
  python manage.py seed_sub_skill_hints
  python manage.py seed_sub_skill_hints --overwrite   # 强制覆盖已有 system_hint
  python manage.py seed_sub_skill_hints --dry-run     # 仅预览，不写入
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.agent.registry import AgentRegistryConfigService
from apps.creation.orchestration.sub_skill_orchestrator import _SUB_SKILL_SYSTEM_HINTS


class Command(BaseCommand):
    help = "把硬编码的子技能 system_hint 写入 AgentRegistryConfig（DB），实现后台可配置"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="强制覆盖 registry 中已有的 system_hint 字段（默认：跳过已有值）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅打印变更预览，不写入数据库",
        )

    def handle(self, *args, **options):
        overwrite: bool = options["overwrite"]
        dry_run: bool = options["dry_run"]

        AgentRegistryConfigService.ensure_defaults()
        row = AgentRegistryConfigService.get_active_row()
        if not row or not isinstance(row.registry, dict):
            self.stderr.write(self.style.ERROR("AgentRegistryConfig 未初始化，请先运行 import_agent_registry_to_db"))
            return

        registry = dict(row.registry)
        agents: list = list(registry.get("agents") or [])

        updated_agents = 0
        updated_skills = 0
        skipped_skills = 0

        for i, agent in enumerate(agents):
            if not isinstance(agent, dict):
                continue
            sub_skills: list = list(agent.get("sub_skills") or [])
            agent_changed = False

            for j, skill in enumerate(sub_skills):
                if not isinstance(skill, dict):
                    continue
                skill_id: str = str(skill.get("id") or "").strip()
                if not skill_id:
                    continue

                hint = _SUB_SKILL_SYSTEM_HINTS.get(skill_id, "")
                if not hint:
                    continue

                existing_hint = (skill.get("system_hint") or "").strip()
                if existing_hint and not overwrite:
                    self.stdout.write(
                        f"  [skip] {agent.get('id')}.{skill_id}：system_hint 已存在（--overwrite 可强制覆盖）"
                    )
                    skipped_skills += 1
                    continue

                action = "覆盖" if existing_hint else "新增"
                self.stdout.write(f"  [{action}] {agent.get('id')}.{skill_id}（{len(hint)} 字符）")

                if not dry_run:
                    updated_skill = dict(skill)
                    updated_skill["system_hint"] = hint
                    sub_skills[j] = updated_skill
                    agent_changed = True
                    updated_skills += 1

            if agent_changed:
                updated_agent = dict(agent)
                updated_agent["sub_skills"] = sub_skills
                agents[i] = updated_agent
                updated_agents += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[dry-run] 预计写入 {updated_skills + skipped_skills} 条 system_hint，跳过 {skipped_skills} 条（已存在）"))
            return

        if not updated_skills:
            self.stdout.write(self.style.WARNING(f"[ok] 无需写入（已全部存在，跳过 {skipped_skills} 条）"))
            return

        registry["agents"] = agents
        row.registry = registry
        row.save(update_fields=["registry", "updated_at"])
        AgentRegistryConfigService._clear_runtime_cache()

        self.stdout.write(
            self.style.SUCCESS(
                f"[ok] 已写入 {updated_skills} 条 system_hint（涉及 {updated_agents} 个 Agent），跳过 {skipped_skills} 条"
            )
        )
