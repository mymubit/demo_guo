# -*- coding: utf-8 -*-
"""
management command: python manage.py snapshot_skill_rules

对 skill-rules/ 目录下所有规则文件创建带时间戳的版本快照，
支持回滚（restore 子命令）。

子命令：
  create [--message "..."]    创建新快照
  list                        列出所有快照
  restore <snapshot_id>       回滚到指定快照
  diff <snapshot_id>          查看快照与当前的差异
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

_SKILL_RULES_FILES = [
    "tier1-iron-rules.json",
    "tier2-genre-rules.json",
    "tier3-workflow-rules.json",
    "tier4-compliance-rules.json",
]
_READONLY_FILES = {"tier1-iron-rules.json", "tier4-compliance-rules.json"}


def _get_rules_root() -> Path:
    root = Path(getattr(settings, "FUSION_SKILL_ROOT", "demo4book"))
    return root / "short-drama-script-creator" / "config" / "skill-rules"


def _get_snapshots_root() -> Path:
    return _get_rules_root() / ".snapshots"


def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()[:8]


class Command(BaseCommand):
    help = "技能规则版本快照管理（创建/列出/回滚/差异对比）"

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="subcommand", help="子命令")

        create_p = subparsers.add_parser("create", help="创建快照")
        create_p.add_argument("--message", "-m", default="", help="快照说明")

        subparsers.add_parser("list", help="列出所有快照")

        restore_p = subparsers.add_parser("restore", help="回滚到指定快照")
        restore_p.add_argument("snapshot_id", help="快照 ID（来自 list 命令）")
        restore_p.add_argument("--dry-run", action="store_true", help="仅显示将要恢复的内容，不实际操作")

        diff_p = subparsers.add_parser("diff", help="查看快照与当前的差异")
        diff_p.add_argument("snapshot_id", help="快照 ID")

    def handle(self, *args, **options):
        subcommand = options.get("subcommand")
        if subcommand == "create" or subcommand is None:
            self._create(options.get("message", ""))
        elif subcommand == "list":
            self._list()
        elif subcommand == "restore":
            self._restore(options["snapshot_id"], dry_run=options.get("dry_run", False))
        elif subcommand == "diff":
            self._diff(options["snapshot_id"])
        else:
            raise CommandError(f"未知子命令: {subcommand}")

    def _create(self, message: str) -> None:
        rules_root = _get_rules_root()
        snapshots_root = _get_snapshots_root()
        snapshots_root.mkdir(parents=True, exist_ok=True)

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        snapshot_id = ts
        snapshot_dir = snapshots_root / snapshot_id
        snapshot_dir.mkdir(exist_ok=True)

        manifest = {
            "snapshot_id": snapshot_id,
            "created_at": datetime.utcnow().isoformat(),
            "message": message,
            "files": {},
        }

        for filename in _SKILL_RULES_FILES:
            src = rules_root / filename
            if not src.exists():
                continue
            dst = snapshot_dir / filename
            shutil.copy2(src, dst)
            manifest["files"][filename] = {
                "hash": _file_hash(src),
                "readonly": filename in _READONLY_FILES,
            }

        manifest_path = snapshot_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(
            f"✓ 快照已创建: {snapshot_id}\n"
            f"  覆盖文件: {list(manifest['files'].keys())}\n"
            f"  说明: {message or '（无）'}"
        ))

    def _list(self) -> None:
        snapshots_root = _get_snapshots_root()
        if not snapshots_root.exists():
            self.stdout.write("暂无快照")
            return

        snapshots = sorted(snapshots_root.iterdir(), reverse=True)
        if not snapshots:
            self.stdout.write("暂无快照")
            return

        self.stdout.write(f"共 {len(snapshots)} 个快照：\n")
        for snap_dir in snapshots:
            manifest_path = snap_dir / "manifest.json"
            if not manifest_path.exists():
                continue
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            files = list(m.get("files", {}).keys())
            self.stdout.write(
                f"  [{m['snapshot_id']}] {m.get('created_at', '')[:16]}"
                f"  {m.get('message', '') or '（无说明）'}"
                f"  文件: {files}"
            )

    def _restore(self, snapshot_id: str, dry_run: bool = False) -> None:
        snapshots_root = _get_snapshots_root()
        snapshot_dir = snapshots_root / snapshot_id

        if not snapshot_dir.exists():
            raise CommandError(f"快照不存在: {snapshot_id}")

        manifest_path = snapshot_dir / "manifest.json"
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        rules_root = _get_rules_root()

        if dry_run:
            self.stdout.write(f"[DRY-RUN] 将恢复以下文件：")
        else:
            # 先创建当前状态的自动快照
            self._create(f"auto-backup before restore {snapshot_id}")

        for filename, info in m.get("files", {}).items():
            if filename in _READONLY_FILES:
                self.stdout.write(self.style.WARNING(f"  跳过只读文件: {filename}"))
                continue
            src = snapshot_dir / filename
            dst = rules_root / filename
            if dry_run:
                self.stdout.write(f"  {filename} (hash={info['hash']})")
            else:
                shutil.copy2(src, dst)
                self.stdout.write(self.style.SUCCESS(f"  ✓ 恢复: {filename}"))

        if not dry_run:
            # 清除热加载缓存
            try:
                from apps.skill.skills.loader import _HOT_RELOAD_MTIME
                _HOT_RELOAD_MTIME.clear()
            except Exception:
                pass
            self.stdout.write(self.style.SUCCESS(f"\n✓ 回滚完成，已清除热加载缓存"))

    def _diff(self, snapshot_id: str) -> None:
        snapshots_root = _get_snapshots_root()
        snapshot_dir = snapshots_root / snapshot_id
        if not snapshot_dir.exists():
            raise CommandError(f"快照不存在: {snapshot_id}")

        rules_root = _get_rules_root()
        manifest_path = snapshot_dir / "manifest.json"
        m = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.stdout.write(f"快照 {snapshot_id} vs 当前状态：\n")
        any_diff = False
        for filename in _SKILL_RULES_FILES:
            current = rules_root / filename
            snap = snapshot_dir / filename
            if not current.exists() and not snap.exists():
                continue
            if not snap.exists():
                self.stdout.write(f"  {filename}: 快照中不存在（当前有）")
                any_diff = True
                continue
            if not current.exists():
                self.stdout.write(f"  {filename}: 当前不存在（快照中有）")
                any_diff = True
                continue
            snap_hash = _file_hash(snap)
            curr_hash = _file_hash(current)
            if snap_hash != curr_hash:
                self.stdout.write(self.style.WARNING(
                    f"  ⚠ {filename}: 已修改 (snap={snap_hash}, current={curr_hash})"
                ))
                any_diff = True
            else:
                self.stdout.write(f"  ✓ {filename}: 无变化")

        if not any_diff:
            self.stdout.write("  所有文件与快照一致，无差异")
