# -*- coding: utf-8 -*-
"""管理命令：将 _SUB_SKILL_SYSTEM_HINTS 硬编码迁移到 AgentSkillDefinition.system_hint

使用：
    python manage.py migrate_system_hints_to_db          # dry-run
    python manage.py migrate_system_hints_to_db --apply  # 真正写入
    python manage.py migrate_system_hints_to_db --apply --overwrite  # 强制覆盖已有 hint

迁移完成后：
  - SkillInvoker._code_fallback_hint 会优先读取 DB，代码层仅作 90 天兼容 fallback
  - 建议迁移后在 Admin 技能管理页逐一核对内容
"""
from __future__ import annotations

import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.creation.orchestration.sub_skill_orchestrator import _SUB_SKILL_SYSTEM_HINTS
from apps.skill.models import AgentSkillDefinition

logger = logging.getLogger(__name__)

# skill_id → 技能元数据（名称、层级、子分类）
_SKILL_META: dict[str, dict] = {
    "structure-generator": {
        "name": "剧本结构生成器",
        "skill_layer": AgentSkillDefinition.LAYER_BUSINESS,
        "sub_category": "大纲",
    },
    "world-builder": {
        "name": "世界观策划师",
        "skill_layer": AgentSkillDefinition.LAYER_BUSINESS,
        "sub_category": "世界观",
    },
    "world-fixer": {
        "name": "世界观修复编辑",
        "skill_layer": AgentSkillDefinition.LAYER_BUSINESS,
        "sub_category": "世界观",
    },
    "character-generator": {
        "name": "人物编剧",
        "skill_layer": AgentSkillDefinition.LAYER_BUSINESS,
        "sub_category": "人设",
    },
    "relationship-weaver": {
        "name": "人物关系编剧",
        "skill_layer": AgentSkillDefinition.LAYER_BUSINESS,
        "sub_category": "人设",
    },
    "hook-planner": {
        "name": "钩子规划师",
        "skill_layer": AgentSkillDefinition.LAYER_BUSINESS,
        "sub_category": "大纲",
    },
    "framework-builder": {
        "name": "大纲框架编剧",
        "skill_layer": AgentSkillDefinition.LAYER_BUSINESS,
        "sub_category": "大纲",
    },
    "episode-outline-writer": {
        "name": "分集大纲编剧",
        "skill_layer": AgentSkillDefinition.LAYER_BUSINESS,
        "sub_category": "大纲",
    },
    "plan-fixer": {
        "name": "大纲修复编辑",
        "skill_layer": AgentSkillDefinition.LAYER_BUSINESS,
        "sub_category": "大纲",
    },
    "episode-script-writer": {
        "name": "分集剧本编剧",
        "skill_layer": AgentSkillDefinition.LAYER_BUSINESS,
        "sub_category": "剧本",
    },
}


class Command(BaseCommand):
    help = "将 _SUB_SKILL_SYSTEM_HINTS 硬编码迁移到 AgentSkillDefinition.system_hint（DB）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="实际写入 DB（默认 dry-run，仅打印变更预览）",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            default=False,
            help="强制覆盖 DB 中已有的 system_hint 内容",
        )

    def handle(self, *args, **options):
        is_apply   = options["apply"]
        overwrite  = options["overwrite"]
        mode_label = "[应用]" if is_apply else "[DRY-RUN]"

        self.stdout.write(f"\n{mode_label} 开始迁移 system_hint，共 {len(_SUB_SKILL_SYSTEM_HINTS)} 条\n")

        created_count  = 0
        updated_count  = 0
        skipped_count  = 0

        for skill_id, system_hint in _SUB_SKILL_SYSTEM_HINTS.items():
            meta = _SKILL_META.get(skill_id, {})
            existing = AgentSkillDefinition.objects.filter(skill_id=skill_id).first()

            if existing:
                if existing.system_hint and not overwrite:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  SKIP  {skill_id!r}（已有 system_hint，使用 --overwrite 强制覆盖）"
                        )
                    )
                    skipped_count += 1
                    continue

                action = "UPDATE"
                if is_apply:
                    fields = ["system_hint", "updated_at"]
                    existing.system_hint = system_hint
                    if meta.get("skill_layer") and not existing.skill_layer:
                        existing.skill_layer = meta["skill_layer"]
                        fields.append("skill_layer")
                    if meta.get("sub_category") and not existing.sub_category:
                        existing.sub_category = meta["sub_category"]
                        fields.append("sub_category")
                    existing.save(update_fields=fields)
                updated_count += 1

            else:
                action = "CREATE"
                if is_apply:
                    with transaction.atomic():
                        AgentSkillDefinition.objects.create(
                            skill_id=skill_id,
                            name=meta.get("name", skill_id),
                            version="1.0.0",
                            category=AgentSkillDefinition.CATEGORY_CREATOR,
                            skill_layer=meta.get("skill_layer", AgentSkillDefinition.LAYER_BUSINESS),
                            sub_category=meta.get("sub_category", ""),
                            lifecycle_status=AgentSkillDefinition.LIFECYCLE_ACTIVE,
                            system_hint=system_hint,
                            content=f"# {meta.get('name', skill_id)}\n\n（由 migrate_system_hints_to_db 自动创建）",
                            is_active=True,
                        )
                created_count += 1

            self.stdout.write(
                self.style.SUCCESS(f"  {action}  {skill_id!r}")
                if is_apply
                else f"  {action}  {skill_id!r}"
            )

        self.stdout.write(
            f"\n{mode_label} 完成 — 创建:{created_count} 更新:{updated_count} 跳过:{skipped_count}\n"
        )
        if not is_apply:
            self.stdout.write(
                self.style.WARNING("  （DRY-RUN 模式，加 --apply 参数后实际写入）\n")
            )
