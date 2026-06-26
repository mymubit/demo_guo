# -*- coding: utf-8 -*-
"""
一条命令从 drama-skills Git SSOT 同步角色、规则并刷新运行时缓存。

用法：
  python manage.py sync_drama_from_git
  python manage.py sync_drama_from_git --force
  python manage.py sync_drama_from_git --dry-run
"""
from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.agent.models import AgentDefinition
from apps.agent.registry import AgentRegistryConfigService
from apps.drama.skills_registry import (
    SKILL_VERSION,
    build_role_defaults,
    clear_registry_cache,
    get_drama_skills_root,
    iter_foundation_rule_files,
    parse_foundation_rule_file,
)
from apps.skill.models import SkillRuleItem, SkillRuleConfig


class Command(BaseCommand):
    help = "从 drama-skills/ 同步角色与规则到数据库，并刷新 SSOT 缓存。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="覆盖已存在的 AgentDefinition 与 SkillRuleItem",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="仅输出 diff 摘要，不写入数据库",
        )
        parser.add_argument(
            "--skip-skills",
            action="store_true",
            default=False,
            help="跳过 seed_drama_skills",
        )
        parser.add_argument(
            "--skip-rules",
            action="store_true",
            default=False,
            help="跳过 seed_drama_rules",
        )

    def handle(self, *args, **options):
        force = options["force"]
        dry_run = options["dry_run"]
        root = get_drama_skills_root()

        self.stdout.write(f"=== drama-skills 同步 ({SKILL_VERSION}) ===")
        self.stdout.write(f"SSOT 根目录: {root}")

        if not root.is_dir():
            self.stdout.write(self.style.ERROR(f"目录不存在: {root}"))
            return

        self._print_pre_sync_summary()

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run：跳过 seed 与缓存刷新"))
            return

        if not options["skip_skills"]:
            self.stdout.write("")
            self.stdout.write(">>> seed_drama_skills")
            call_command(
                "seed_drama_skills",
                force=force,
                stdout=self.stdout,
                stderr=self.stderr,
            )

        if not options["skip_rules"]:
            self.stdout.write("")
            self.stdout.write(">>> seed_drama_rules")
            call_command(
                "seed_drama_rules",
                force=force,
                stdout=self.stdout,
                stderr=self.stderr,
            )

        clear_registry_cache()
        AgentRegistryConfigService.clear_cache()
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("已刷新 skills_registry 与 AgentRegistry 缓存"))

        self.stdout.write("")
        self._print_post_sync_summary()

    def _print_pre_sync_summary(self) -> None:
        ssot_roles = {r["agent_id"] for r in build_role_defaults()}
        db_roles = set(
            AgentDefinition.objects.filter(
                category="drama_skills",
                agent_id__startswith="drama.",
            ).values_list("agent_id", flat=True)
        )
        missing_in_db = sorted(ssot_roles - db_roles)
        stale_in_db = sorted(db_roles - ssot_roles)

        rule_files = iter_foundation_rule_files()
        ssot_rule_keys: set[str] = set()
        for path in rule_files:
            for row in parse_foundation_rule_file(path):
                ssot_rule_keys.add(row["rule_key"])

        db_rule_keys = set(
            SkillRuleItem.objects.filter(
                status=SkillRuleConfig.STATUS_ACTIVE,
                rule_key__startswith="t",
            ).values_list("rule_key", flat=True)
        )
        missing_rules = sorted(ssot_rule_keys - db_rule_keys)

        self.stdout.write("")
        self.stdout.write("--- 同步前 diff ---")
        self.stdout.write(f"  SSOT 角色: {len(ssot_roles)} · DB 角色: {len(db_roles)}")
        if missing_in_db:
            self.stdout.write(self.style.WARNING(f"  DB 缺失角色 ({len(missing_in_db)}): {', '.join(missing_in_db[:5])}"
                                                   + (" …" if len(missing_in_db) > 5 else "")))
        if stale_in_db:
            self.stdout.write(self.style.WARNING(f"  DB 多余角色 ({len(stale_in_db)}): {', '.join(stale_in_db[:5])}"
                                                   + (" …" if len(stale_in_db) > 5 else "")))
        if not missing_in_db and not stale_in_db:
            self.stdout.write("  角色: DB 与 SSOT 一致")

        self.stdout.write(f"  SSOT 规则: {len(ssot_rule_keys)} · DB active 规则: {len(db_rule_keys)}")
        if missing_rules:
            self.stdout.write(self.style.WARNING(f"  DB 缺失规则 ({len(missing_rules)} 条)"))
        elif len(ssot_rule_keys) != len(db_rule_keys):
            self.stdout.write("  规则: 条目数不一致（可能已有覆盖版本，--force 可全量刷新）")
        else:
            self.stdout.write("  规则: DB 与 SSOT 条目数一致")

    def _print_post_sync_summary(self) -> None:
        ssot_count = len(build_role_defaults())
        db_count = AgentDefinition.objects.filter(
            category="drama_skills",
            agent_id__startswith="drama.",
        ).count()
        active_rules = SkillRuleItem.objects.filter(
            status=SkillRuleConfig.STATUS_ACTIVE,
        ).count()

        self.stdout.write("--- 同步后状态 ---")
        self.stdout.write(f"  AgentDefinition (drama.*): {db_count} / SSOT {ssot_count}")
        self.stdout.write(f"  SkillRuleItem (active): {active_rules}")
        if db_count == ssot_count:
            self.stdout.write(self.style.SUCCESS("  角色同步完成"))
        else:
            self.stdout.write(self.style.WARNING("  角色数量仍不一致，请检查 seed 日志"))
