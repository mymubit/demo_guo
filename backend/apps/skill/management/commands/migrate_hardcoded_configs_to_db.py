# -*- coding: utf-8 -*-
"""管理命令：将硬编码配置（合规规则 / 收敛阈值）迁移到 SkillConfigEntry

迁移内容：
  1. brief.compliance_rules  — 来自 brief_engine._BRIEF_P0_PATTERNS / _BRIEF_P1_WARNINGS
  2. convergence.thresholds  — 来自磁盘 skill-thresholds.json（若存在）

使用：
    python manage.py migrate_hardcoded_configs_to_db          # dry-run
    python manage.py migrate_hardcoded_configs_to_db --apply  # 真正写入
    python manage.py migrate_hardcoded_configs_to_db --apply --overwrite  # 覆盖已有
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.skill.models import SkillConfigEntry

logger = logging.getLogger(__name__)

# 合规规则配置键
CONFIG_KEY_COMPLIANCE = "brief.compliance_rules"
CONFIG_KEY_THRESHOLDS = "convergence.thresholds"


def _load_compliance_rules() -> dict:
    """从代码中提取合规规则，转换为可存储的结构（兼容：旧引擎已下线时返回空 dict）"""
    try:
        from apps.creation.orchestration.brief_engine import (
            _BRIEF_P0_PATTERNS,
            _BRIEF_P1_WARNINGS,
        )
        return {
            "p0_patterns": [
                {"pattern": p, "label": label}
                for p, label in _BRIEF_P0_PATTERNS
            ],
            "p1_warnings": [
                {"pattern": p, "label": label}
                for p, label in _BRIEF_P1_WARNINGS
            ],
            "_note": "P0 触发即熔断；P1 注入合规提示",
        }
    except ImportError as exc:
        logger.warning(
            "无法加载合规规则（旧引擎 brief_engine 已下线，规则已迁移到 DB / skill 层）: %s", exc,
        )
        return {}


def _load_convergence_thresholds() -> dict:
    """从磁盘 skill-thresholds.json 加载收敛阈值（若存在）"""
    search_paths = [
        Path(__file__).parents[6] / "ai-drama-skills-v2" / "config" / "skill-thresholds.json",
        Path(__file__).parents[7] / "demo4book" / "ai-drama-skills-v2" / "config" / "skill-thresholds.json",
    ]
    for path in search_paths:
        if path.exists():
            try:
                with path.open(encoding="utf-8") as f:
                    return json.load(f)
            except Exception as exc:  # noqa: BLE001
                logger.warning("读取 %s 失败: %s", path, exc)
    logger.info("未找到 skill-thresholds.json，使用内置默认值")
    return {
        "convergence": {
            "max_fix_rounds": 2,
            "stagnate_threshold": 1,
            "oscillate_window": 3,
            "score_pass_threshold": 75,
        },
        "_note": "由 migrate_hardcoded_configs_to_db 生成的默认值",
    }


class Command(BaseCommand):
    help = "将硬编码合规规则与收敛阈值迁移到 SkillConfigEntry（配置中心）"

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", default=False)
        parser.add_argument("--overwrite", action="store_true", default=False)

    def handle(self, *args, **options):
        is_apply  = options["apply"]
        overwrite = options["overwrite"]
        label     = "[应用]" if is_apply else "[DRY-RUN]"

        configs = [
            (CONFIG_KEY_COMPLIANCE, "合规规则（P0/P1）", _load_compliance_rules()),
            (CONFIG_KEY_THRESHOLDS, "收敛阈值配置",     _load_convergence_thresholds()),
        ]

        for config_key, desc, content in configs:
            self.stdout.write(f"\n{label} 迁移 {desc}（key={config_key!r}）")

            if not content:
                self.stdout.write(self.style.WARNING(f"  内容为空，跳过"))
                continue

            existing = SkillConfigEntry.objects.filter(config_key=config_key).first()
            if existing:
                if not overwrite:
                    self.stdout.write(self.style.WARNING(f"  SKIP（已存在，使用 --overwrite 强制覆盖）"))
                    continue
                action = "UPDATE"
                if is_apply:
                    existing.content = content
                    existing.save(update_fields=["content", "updated_at"])
            else:
                action = "CREATE"
                if is_apply:
                    with transaction.atomic():
                        SkillConfigEntry.objects.create(
                            config_key=config_key,
                            edition="unified",
                            version="1.0.0",
                            content=content,
                            note=f"由 migrate_hardcoded_configs_to_db 自动迁移 — {desc}",
                        )

            self.stdout.write(
                self.style.SUCCESS(f"  {action}  {config_key!r}")
                if is_apply else f"  {action}  {config_key!r}"
            )

        self.stdout.write(f"\n{label} 迁移完成\n")
        if not is_apply:
            self.stdout.write(self.style.WARNING("  （DRY-RUN 模式，加 --apply 参数后实际写入）\n"))
