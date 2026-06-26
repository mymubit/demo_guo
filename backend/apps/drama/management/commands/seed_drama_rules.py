# -*- coding: utf-8 -*-
"""
从 drama-skills/foundation/rules/ 种入 SkillRuleItem 规则条目。

用法：
  python manage.py seed_drama_rules
  python manage.py seed_drama_rules --force
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.drama.skills_registry import (
    SKILL_VERSION,
    get_drama_skills_root,
    iter_foundation_rule_files,
    parse_foundation_rule_file,
)
from apps.skill.models import SkillRuleConfig, SkillRuleItem


class Command(BaseCommand):
    help = "从 drama-skills/foundation/rules/ 同步 Tier1-4 规则条目到 SkillRuleItem。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="覆盖已存在的 active 规则（按 rule_key 归档旧版后写入）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="仅统计，不写入数据库",
        )

    def handle(self, *args, **options):
        force = options["force"]
        dry_run = options["dry_run"]
        root = get_drama_skills_root()
        files = iter_foundation_rule_files()

        if not files:
            self.stdout.write(self.style.ERROR(f"未找到规则文件: {root / 'foundation' / 'rules'}"))
            return

        self.stdout.write(f"SSOT {SKILL_VERSION} · 扫描 {len(files)} 个规则文件")

        created = 0
        updated = 0
        skipped = 0
        total_items = 0

        with transaction.atomic():
            for path in files:
                rows = parse_foundation_rule_file(path)
                total_items += len(rows)
                rel = path.relative_to(root).as_posix()
                self.stdout.write(f"  {rel}: {len(rows)} 条")

                if dry_run:
                    continue

                for row in rows:
                    existing = SkillRuleItem.objects.filter(
                        rule_key=row["rule_key"],
                        status=SkillRuleConfig.STATUS_ACTIVE,
                    ).first()

                    if existing and not force:
                        skipped += 1
                        continue

                    if existing and force:
                        existing.status = SkillRuleConfig.STATUS_ARCHIVED
                        existing.save(update_fields=["status", "updated_at"])

                    SkillRuleItem.objects.create(
                        rule_key=row["rule_key"],
                        tier=row["tier"],
                        scope_type=row["scope_type"],
                        scope_key=row["scope_key"],
                        section=row["section"],
                        title=row["title"],
                        body=row["body"],
                        priority=row["priority"],
                        sort_order=row["sort_order"],
                        version_tag=row["version_tag"],
                        status=SkillRuleConfig.STATUS_ACTIVE,
                        source=SkillRuleConfig.SOURCE_ADMIN,
                        note=row["source_note"],
                    )
                    if existing:
                        updated += 1
                    else:
                        created += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry run：共 {total_items} 条规则条目"))
            return

        self.stdout.write(self.style.SUCCESS(
            f"完成！新建 {created} 条，覆盖 {updated} 条，跳过 {skipped} 条（共扫描 {total_items} 条）"
        ))
