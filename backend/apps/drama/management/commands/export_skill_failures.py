# -*- coding: utf-8 -*-
"""从 LLM 调用日志导出结构化失败样本，供写入 anti-examples.yaml。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Q

from apps.drama.models import DramaLlmCallLog


class Command(BaseCommand):
    help = "导出 json_repair / schema 失败相关的 LLM 调用，沉淀为技能反例草稿"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--output",
            type=Path,
            default=Path("skill_failure_export.json"),
            help="导出 JSON 路径",
        )
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--role", default="", help="过滤 agent_id")

    def handle(self, *args: Any, **options: Any) -> None:
        limit = int(options["limit"])
        role = (options.get("role") or "").strip()
        qs = DramaLlmCallLog.objects.filter(
            Q(purpose__icontains="json_repair")
            | Q(status=DramaLlmCallLog.Status.ERROR)
            | Q(error_message__icontains="Schema")
            | Q(error_message__icontains="JSON")
        ).order_by("-created_at")
        if role:
            qs = qs.filter(role=role)

        rows: list[dict[str, Any]] = []
        for log in qs[:limit]:
            response_preview = (log.response_text or "")[:1200]
            rows.append(
                {
                    "id": str(log.id),
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                    "role": log.role,
                    "purpose": log.purpose,
                    "status": log.status,
                    "error_message": log.error_message,
                    "model_name": log.model_name,
                    "response_preview": response_preview,
                    "suggested_anti_example": {
                        "id": f"AUTO-{str(log.id)[:8]}",
                        "severity": "high" if log.status == "error" else "medium",
                        "title": (log.error_message or log.purpose or "structured_fail")[:120],
                        "note": "请人工审阅后合并进 roles/*/anti-examples.yaml",
                        "raw_error": log.error_message,
                    },
                }
            )

        out: Path = options["output"]
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"已导出 {len(rows)} 条 → {out}"))
