# -*- coding: utf-8 -*-
"""存量项目 artifact 规则补全（不调用 LLM）。"""
from __future__ import annotations

import copy

from django.core.management.base import BaseCommand

from apps.creation.artifact_service import get_artifact, save_artifact
from apps.creation.models import Project
from apps.creation.outline_enrichment import enrich_outline_payload
from apps.creation.display.structure_display import enrich_structure_payload


class Command(BaseCommand):
    help = "对存量 fusion artifact 执行规则补全（六阶段/节奏/反转/creativePlan 等），不消耗 LLM"

    def add_arguments(self, parser):
        parser.add_argument("--project-id", type=str, default="", help="仅处理指定 project UUID")
        parser.add_argument("--limit", type=int, default=200, help="最多处理条数")
        parser.add_argument(
            "--targets",
            type=str,
            default="structure,outline",
            help="逗号分隔：structure / outline / all",
        )
        parser.add_argument("--dry-run", action="store_true", help="仅统计，不写库")

    def handle(self, *args, **options):
        targets = {t.strip().lower() for t in (options["targets"] or "").split(",") if t.strip()}
        if "all" in targets:
            targets = {"structure", "outline"}

        qs = Project.objects.filter(pipeline_mode=Project.MODE_WORKSPACE).order_by("-updated_at")
        if options["project_id"]:
            qs = qs.filter(id=options["project_id"])
        projects = list(qs[: options["limit"]])

        touched = 0
        for project in projects:
            changed = self._enrich_project(
                project,
                targets=targets,
                dry_run=options["dry_run"],
            )
            if changed:
                touched += 1
                flag = "DRY" if options["dry_run"] else "OK"
                self.stdout.write(self.style.SUCCESS(f"{flag} {project.id} · {project.title or project.theme}"))

        self.stdout.write(
            self.style.NOTICE(
                f"扫描 {len(projects)} 个，{'将更新' if options['dry_run'] else '已更新'} {touched} 个"
            )
        )

    def _enrich_project(self, project: Project, *, targets: set, dry_run: bool) -> bool:
        changed = False
        theme = project.theme or ""
        total_eps = int(project.episode_count or 80)

        if "structure" in targets:
            raw = get_artifact(project, "structure_plan")
            if isinstance(raw, dict) and raw:
                enriched = enrich_structure_payload(
                    copy.deepcopy(raw),
                    theme=theme,
                    episode_count=total_eps,
                )
                if enriched != raw:
                    changed = True
                    if not dry_run:
                        save_artifact(project, "structure_plan", enriched)

        structure = get_artifact(project, "structure_plan") or {}
        character_bible = get_artifact(project, "character_bible") or {}
        brief = get_artifact(project, "project_brief") or {}

        if "outline" in targets:
            raw = get_artifact(project, "series_outline")
            if isinstance(raw, dict) and raw:
                enriched = enrich_outline_payload(
                    copy.deepcopy(raw),
                    structure_plan=structure,
                    character_bible=character_bible,
                    project_brief=brief,
                    theme=theme,
                    total_episodes=total_eps,
                )
                if enriched != raw:
                    changed = True
                    if not dry_run:
                        save_artifact(project, "series_outline", enriched)

        return changed
