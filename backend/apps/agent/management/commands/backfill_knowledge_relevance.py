"""
回填知识项相关性元数据：

1. 按 category 标注 is_prompt_injectable（validator/schema 仅供校验层，置 False）；
2. 尽力从来源路径/标题推断 match_platforms（命中已知平台关键词时）；
3. match_themes/match_genres 默认留空（=通用），由后台精细化配置。

用法：
  python manage.py backfill_knowledge_relevance --dry-run   # 仅预览统计
  python manage.py backfill_knowledge_relevance --commit    # 实际写入
"""
from __future__ import annotations

from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.agent.models import AgentKnowledgeItem

# 仅供校验层使用、不进入 prompt 的知识类别
NON_INJECTABLE_CATEGORIES = {
    AgentKnowledgeItem.Category.VALIDATOR,
    AgentKnowledgeItem.Category.SCHEMA,
}

# 路径/标题中的平台关键词 -> 标准平台值
PLATFORM_KEYWORDS = {
    "douyin": "douyin",
    "抖音": "douyin",
    "kuaishou": "kuaishou",
    "快手": "kuaishou",
    "wechat": "wechat",
    "微信": "wechat",
    "视频号": "wechat",
}


def _infer_platforms(*texts: str) -> list[str]:
    haystack = " ".join(t.lower() for t in texts if t)
    hits = {value for keyword, value in PLATFORM_KEYWORDS.items() if keyword in haystack}
    return sorted(hits)


class Command(BaseCommand):
    help = "回填知识项相关性元数据（is_prompt_injectable / match_platforms）"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入")
        parser.add_argument("--commit", action="store_true", help="实际写入数据库")

    def handle(self, *args, **options):
        if options["dry_run"] == options["commit"]:
            raise CommandError("请且仅指定 --dry-run 或 --commit 其中之一")

        summary = Counter()
        updates: list[AgentKnowledgeItem] = []
        for item in AgentKnowledgeItem.objects.all().iterator():
            changed = False
            should_inject = item.category not in NON_INJECTABLE_CATEGORIES
            if item.is_prompt_injectable != should_inject:
                item.is_prompt_injectable = should_inject
                changed = True
                summary["injectable_flag_changed"] += 1

            if not item.match_platforms:
                platforms = _infer_platforms(item.source_path, item.knowledge_id, item.title)
                if platforms:
                    item.match_platforms = platforms
                    changed = True
                    summary["platforms_inferred"] += 1

            if changed:
                updates.append(item)

        summary["total_scanned"] = AgentKnowledgeItem.objects.count()
        summary["to_update"] = len(updates)

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("[dry-run] 预览统计："))
            for key, value in summary.items():
                self.stdout.write(f"  {key}: {value}")
            return

        with transaction.atomic():
            for item in updates:
                item.save(update_fields=["is_prompt_injectable", "match_platforms", "updated_at"])

        self.stdout.write(self.style.SUCCESS("回填完成："))
        for key, value in summary.items():
            self.stdout.write(f"  {key}: {value}")
