# -*- coding: utf-8 -*-
"""管理命令：将 SKILL.md 文件批量导入 AgentSkillDefinition 表。

扫描路径：
  - <workspace>/ai-drama-skills-v2/drama-*/SKILL.md
  - <workspace>/ai-drama-skills-v2/*/SKILL.md（兜底）

frontmatter 解析规则（YAML 块 --- ... ---）：
  name       → AgentSkillDefinition.name
  version    → AgentSkillDefinition.version
  category   → AgentSkillDefinition.category（映射 creator/quality/compliance/shared）
  skill_id   → AgentSkillDefinition.skill_id（否则取目录名）

用法：
  python manage.py import_skills_to_db
  python manage.py import_skills_to_db --root /path/to/ai-drama-skills-v2
  python manage.py import_skills_to_db --dry-run
  python manage.py import_skills_to_db --force-overwrite
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand

from apps.skill.models import AgentSkillDefinition

# 目录名 → category 映射（兜底）
_DIR_CATEGORY_MAP = {
    "creator": AgentSkillDefinition.CATEGORY_CREATOR,
    "quality": AgentSkillDefinition.CATEGORY_QUALITY,
    "compliance": AgentSkillDefinition.CATEGORY_COMPLIANCE,
    "shared": AgentSkillDefinition.CATEGORY_SHARED,
    "drama-creator": AgentSkillDefinition.CATEGORY_CREATOR,
    "drama-quality": AgentSkillDefinition.CATEGORY_QUALITY,
    "drama-compliance": AgentSkillDefinition.CATEGORY_COMPLIANCE,
}

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(content: str) -> dict:
    """简单提取 YAML frontmatter（仅支持 key: value 单行格式）。"""
    m = _FRONTMATTER_RE.match(content)
    if not m:
        return {}
    result = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def _infer_category(fm: dict, dir_name: str) -> str:
    if "category" in fm:
        return fm["category"]
    for key, cat in _DIR_CATEGORY_MAP.items():
        if key in dir_name:
            return cat
    return AgentSkillDefinition.CATEGORY_CREATOR


def _infer_skill_id(fm: dict, dir_name: str) -> str:
    return fm.get("skill_id") or fm.get("name", "").lower().replace(" ", "-") or dir_name


class Command(BaseCommand):
    help = "批量导入 SKILL.md 文件到 AgentSkillDefinition 数据表"

    def add_arguments(self, parser):
        parser.add_argument(
            "--root",
            type=str,
            default="",
            help="ai-drama-skills-v2 根目录（默认自动从项目根推导）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅列出将要导入的文件，不写入数据库",
        )
        parser.add_argument(
            "--force-overwrite",
            action="store_true",
            help="已存在的记录也更新 content（默认跳过）",
        )

    def handle(self, *args, **options):
        root_arg: str = options.get("root") or ""
        dry_run: bool = options["dry_run"]
        force: bool = options["force_overwrite"]

        # 推导根目录
        if root_arg:
            scan_root = Path(root_arg)
        else:
            # backend → ScriptForge → flickplay
            workspace = Path(__file__).resolve().parents[6]
            scan_root = workspace / "ai-drama-skills-v2"

        if not scan_root.exists():
            self.stderr.write(self.style.ERROR(f"路径不存在: {scan_root}"))
            return

        skill_files = sorted(scan_root.rglob("SKILL.md"))
        self.stdout.write(f"扫描到 {len(skill_files)} 个 SKILL.md，根目录: {scan_root}")

        created = updated = skipped = 0

        for fpath in skill_files:
            try:
                content = fpath.read_text(encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"  读取失败: {fpath}  ({exc})")
                continue

            fm = _parse_frontmatter(content)
            dir_name = fpath.parent.name
            skill_id = _infer_skill_id(fm, dir_name)
            name = fm.get("name") or skill_id
            version = fm.get("version") or "1.0.0"
            category = _infer_category(fm, dir_name)
            rel_path = str(fpath.relative_to(scan_root.parent))

            if dry_run:
                self.stdout.write(f"  [DRY] {skill_id}  category={category}  v{version}  {rel_path}")
                created += 1
                continue

            obj, is_created = AgentSkillDefinition.objects.get_or_create(
                skill_id=skill_id,
                defaults={
                    "name": name,
                    "version": version,
                    "category": category,
                    "content": content,
                    "source_file": rel_path,
                },
            )

            if is_created:
                self.stdout.write(self.style.SUCCESS(f"  [新建] {skill_id}"))
                created += 1
            elif force:
                obj.name = name
                obj.version = version
                obj.category = category
                obj.content = content
                obj.source_file = rel_path
                obj.save(update_fields=["name", "version", "category", "content", "source_file", "updated_at"])
                self.stdout.write(f"  [更新] {skill_id}")
                updated += 1
            else:
                skipped += 1

        label = "（DRY RUN）" if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"\n完成{label}：新建 {created}  更新 {updated}  跳过 {skipped}"
        ))
