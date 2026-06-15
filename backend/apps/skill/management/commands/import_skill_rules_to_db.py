"""
将 skill-rules/ 目录下的 tier2-genre-rules.json / tier3-workflow-rules.json
一次性导入到 SkillRuleConfig 数据库表（status=active, source=file_import）。

用法：
  python manage.py import_skill_rules_to_db              # 导入（跳过已存在 active 记录）
  python manage.py import_skill_rules_to_db --overwrite  # 强制覆盖（旧记录变 archived）
"""
import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.skill.models import SkillRuleConfig

logger = logging.getLogger(__name__)

_SKILL_RULES_DIR = (
    Path(__file__).resolve().parents[6]
    / "demo4book"
    / "short-drama-script-creator"
    / "config"
    / "skill-rules"
)


def _import_tier2(data: dict, overwrite: bool, dry_run: bool, stdout) -> int:
    """导入 tier2-genre-rules.json：每个 genre → 一条 DB 记录。"""
    count = 0
    genres = data.get("genres") or {}
    for genre_key, genre_data in genres.items():
        if isinstance(genre_data, dict) and "$ref" in genre_data:
            continue  # 跳过引用别名

        existing = SkillRuleConfig.objects.filter(
            tier=2,
            scope_type=SkillRuleConfig.SCOPE_GENRE,
            scope_key=genre_key,
            section="genre_full",
            status=SkillRuleConfig.STATUS_ACTIVE,
        ).first()

        if existing and not overwrite:
            stdout.write(f"  [skip] tier2·{genre_key} 已有 active 记录")
            continue

        if dry_run:
            stdout.write(f"  [dry-run] 将导入 tier2·{genre_key}")
            count += 1
            continue

        if existing and overwrite:
            existing.status = SkillRuleConfig.STATUS_ARCHIVED
            existing.save(update_fields=["status", "updated_at"])

        SkillRuleConfig.objects.create(
            tier=2,
            scope_type=SkillRuleConfig.SCOPE_GENRE,
            scope_key=genre_key,
            section="genre_full",
            content=genre_data,
            version_tag=data.get("_meta", {}).get("version", "v5.0.0"),
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_FILE,
            note=f"从 tier2-genre-rules.json 导入·{genre_data.get('label', genre_key)}",
            approved_by="system_import",
        )
        stdout.write(f"  [ok] tier2·{genre_key}")
        count += 1
    return count


def _import_tier3(data: dict, overwrite: bool, dry_run: bool, stdout) -> int:
    """导入 tier3-workflow-rules.json：每个 pipeline node → 一条 DB 记录。"""
    count = 0
    pipeline = list(data.get("main_pipeline") or []) + list(data.get("optional_nodes") or [])
    for node_def in pipeline:
        node_id = node_def.get("node_id") or ""
        if not node_id:
            continue

        existing = SkillRuleConfig.objects.filter(
            tier=3,
            scope_type=SkillRuleConfig.SCOPE_NODE,
            scope_key=node_id,
            section="pipeline_node_full",
            status=SkillRuleConfig.STATUS_ACTIVE,
        ).first()

        if existing and not overwrite:
            stdout.write(f"  [skip] tier3·{node_id} 已有 active 记录")
            continue

        if dry_run:
            stdout.write(f"  [dry-run] 将导入 tier3·{node_id}")
            count += 1
            continue

        if existing and overwrite:
            existing.status = SkillRuleConfig.STATUS_ARCHIVED
            existing.save(update_fields=["status", "updated_at"])

        SkillRuleConfig.objects.create(
            tier=3,
            scope_type=SkillRuleConfig.SCOPE_NODE,
            scope_key=node_id,
            section="pipeline_node_full",
            content=node_def,
            version_tag=data.get("_meta", {}).get("version", "v5.0.0"),
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_FILE,
            note=f"从 tier3-workflow-rules.json 导入·{node_def.get('name', node_id)}",
            approved_by="system_import",
        )
        stdout.write(f"  [ok] tier3·{node_id}")
        count += 1
    return count


class Command(BaseCommand):
    help = "将 skill-rules/tier2 和 tier3 JSON 文件导入 SkillRuleConfig 数据库"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            default=False,
            help="覆盖已有 active 记录（旧版归档）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="仅预览，不写入数据库",
        )
        parser.add_argument(
            "--rules-dir",
            type=str,
            default="",
            help="skill-rules 目录路径（默认自动定位）",
        )

    def handle(self, *args, **options):
        from apps.skill.skills.admin_service import SkillRuleConfigService

        overwrite = options["overwrite"]
        dry_run = options["dry_run"]
        rules_dir = Path(options["rules_dir"]) if options["rules_dir"] else _SKILL_RULES_DIR

        if not rules_dir.exists():
            self.stderr.write(f"[error] skill-rules 目录不存在: {rules_dir}")
            return

        self.stdout.write(f"skill-rules 目录: {rules_dir}")
        self.stdout.write(f"模式: {'dry-run' if dry_run else ('overwrite' if overwrite else 'skip-existing')}")

        if dry_run:
            self.stdout.write("[dry-run] 请去掉 --dry-run 以实际导入")
            return

        counts = SkillRuleConfigService.import_from_files(rules_dir=rules_dir, overwrite=overwrite)
        total = sum(counts.values())
        self.stdout.write(f"\n完成，共处理 {total} 条：{counts}")
        self.stdout.write("后续可在「流水线配置 → 技能规则」或 Django Admin 中编辑")
