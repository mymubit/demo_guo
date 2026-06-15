# -*- coding: utf-8 -*-
"""管理命令：将 config/*.json 文件批量导入 SkillConfigEntry 表。

扫描路径（按优先级，demo4book 优先）：
  1. <workspace>/demo4book/short-drama-script-creator/config/*.json
  2. <workspace>/ai-drama-skills-v2/config/*.json

排除已有专项导入命令处理的文件：
  - skill-rules*.json（由 import_skill_rules 命令处理）

用法：
  python manage.py import_configs_to_db
  python manage.py import_configs_to_db --source=ai-drama-skills-v2
  python manage.py import_configs_to_db --source=demo4book
  python manage.py import_configs_to_db --dry-run
  python manage.py import_configs_to_db --force-overwrite
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand

from apps.skill.models import SkillConfigEntry

_EXCLUDE_PATTERNS = ("skill-rules",)

_SOURCE_EDITION_MAP = {
    "demo4book": "demo4book",
    "ai-drama-skills-v2": "ai-drama-skills-v2",
}


def _should_exclude(stem: str) -> bool:
    return any(p in stem for p in _EXCLUDE_PATTERNS)


class Command(BaseCommand):
    help = "批量导入 config/*.json 配置文件到 SkillConfigEntry 数据表"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=["demo4book", "ai-drama-skills-v2", "both"],
            default="both",
            help="扫描来源（默认 both，demo4book 优先）",
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

    def _get_workspace(self) -> Path:
        return Path(__file__).resolve().parents[6]

    def _collect_files(self, source: str, workspace: Path) -> list[tuple[Path, str]]:
        """返回 (json_path, edition) 列表，已去重（按 config_key，先出现的优先）。"""
        candidates: dict[str, tuple[Path, str]] = {}

        def _scan(base: Path, edition: str) -> None:
            config_dir = base / "config"
            if not config_dir.exists():
                return
            for fpath in sorted(config_dir.glob("*.json")):
                if _should_exclude(fpath.stem):
                    continue
                key = fpath.stem
                if key not in candidates:
                    candidates[key] = (fpath, edition)

        if source in ("demo4book", "both"):
            _scan(workspace / "demo4book" / "short-drama-script-creator", "demo4book")
        if source in ("ai-drama-skills-v2", "both"):
            _scan(workspace / "ai-drama-skills-v2", "ai-drama-skills-v2")

        return list(candidates.values())

    def handle(self, *args, **options):
        source: str = options["source"]
        dry_run: bool = options["dry_run"]
        force: bool = options["force_overwrite"]

        workspace = self._get_workspace()
        pairs = self._collect_files(source, workspace)

        self.stdout.write(f"收集到 {len(pairs)} 个配置文件（来源: {source}）")

        created = updated = skipped = error = 0

        for fpath, edition in pairs:
            config_key = fpath.stem
            try:
                raw = fpath.read_text(encoding="utf-8")
                content = json.loads(raw)
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"  [ERROR] {fpath.name}: {exc}")
                error += 1
                continue

            version = (
                content.get("_version")
                or content.get("version")
                or "1.0.0"
            )
            if not isinstance(version, str):
                version = str(version)

            if dry_run:
                self.stdout.write(f"  [DRY] {config_key}  edition={edition}  v{version}")
                created += 1
                continue

            obj, is_created = SkillConfigEntry.objects.get_or_create(
                config_key=config_key,
                defaults={
                    "edition": edition,
                    "version": version,
                    "content": content,
                },
            )

            if is_created:
                self.stdout.write(self.style.SUCCESS(f"  [新建] {config_key}  ({edition})"))
                created += 1
            elif force:
                obj.edition = edition
                obj.version = version
                obj.content = content
                obj.save(update_fields=["edition", "version", "content", "updated_at"])
                self.stdout.write(f"  [更新] {config_key}  ({edition})")
                updated += 1
            else:
                skipped += 1

        label = "（DRY RUN）" if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"\n完成{label}：新建 {created}  更新 {updated}  跳过 {skipped}  错误 {error}"
        ))
