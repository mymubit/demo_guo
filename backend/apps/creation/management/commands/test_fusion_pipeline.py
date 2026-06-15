# -*- coding: utf-8 -*-
"""本地验证：融合后处理（不依赖 DB/Celery）。"""
import json

from django.core.management.base import BaseCommand

from apps.creation.fusion.fusion_pipeline import scripts_result_to_markdown, run_fusion_for_project
from apps.creation.engine.pipeline import run_full_pipeline


class Command(BaseCommand):
    help = "运行 LLM 流水线 + 融合 gate/score（需有效会员项目或 --dry-cli）"

    def add_arguments(self, parser):
        parser.add_argument("--dry-cli", action="store_true", help="仅测剧本转 MD + gate CLI")

    def handle(self, *args, **options):
        if options["dry_cli"]:
            from pathlib import Path
            from django.conf import settings
            from apps.workflow.fusion import FusionCliRunner

            sample = Path(settings.BASE_DIR).parent.parent / "demo4book" / "short-drama-script-creator" / "runtime" / "fixtures" / "sample-ep1.md"
            if not sample.is_file():
                self.stderr.write("sample-ep1.md 不存在")
                return
            r = FusionCliRunner().gate_full(sample, strict=False)
            self.stdout.write(json.dumps(r.get("json") or {"stdout": r.get("stdout")}, ensure_ascii=False, indent=2))
            return

        result = run_full_pipeline(
            {
                "theme": "family-revenge",
                "core_idea": "女主带合同对峙豪门，身份反转",
                "episode_count": 10,
                "format_variant": "B",
            }
        )
        md = scripts_result_to_markdown(result.get("scripts") or {})
        self.stdout.write(f"剧本 MD 长度: {len(md)}")
        self.stdout.write(json.dumps({"status": result.get("status"), "episodes": (result.get("scripts") or {}).get("total_episodes")}, ensure_ascii=False))
