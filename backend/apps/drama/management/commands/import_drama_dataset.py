# -*- coding: utf-8 -*-
"""导入脱敏后的真实短剧项目数据。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.core.schema_validator import SchemaValidator
from apps.drama.services.artifact_service import ArtifactService
from apps.drama.services.project_settings import ProjectSettingsService


class Command(BaseCommand):
    help = "导入符合当前 Schema 的脱敏项目、流程状态和产物"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("dataset", type=Path)
        parser.add_argument("--owner", required=True)
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        dataset_path: Path = options["dataset"]
        if not dataset_path.exists():
            raise CommandError(f"数据文件不存在: {dataset_path}")
        try:
            payload = json.loads(dataset_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"数据文件不是合法 JSON: {exc}") from exc

        projects = payload.get("projects")
        if not isinstance(projects, list) or not projects:
            raise CommandError("数据文件必须包含非空 projects 数组")

        try:
            owner = get_user_model().objects.get(username=options["owner"])
        except get_user_model().DoesNotExist as exc:
            raise CommandError(f"用户不存在: {options['owner']}") from exc

        settings_service = ProjectSettingsService()
        artifact_service = ArtifactService()
        schema_validator = SchemaValidator()
        imported = 0

        for item in projects:
            settings = item.get("settings") or {}
            title = settings.get("title") or item.get("title")
            entry_type = settings.get("entry_type", "original_track")
            if not title:
                raise CommandError("每个项目必须包含 title")

            project = settings_service.create_project(
                owner,
                title,
                entry_type=entry_type,
            )
            settings_service.update_settings(
                project,
                settings,
                expected_revision=1,
                actor=owner.username,
            )

            for artifact in item.get("artifacts") or []:
                artifact_key = artifact["artifact_key"]
                schema_version = artifact.get("schema_version")
                if schema_version is not None and not isinstance(schema_version, int):
                    from apps.drama.services.skills_loader import get_skills_loader

                    loader = get_skills_loader()
                    if loader.get_artifact_contract(artifact_key).get("schema_version"):
                        schema_version = loader.artifact_schema_version(artifact_key)
                    else:
                        schema_version = int(schema_version)
                artifact_service.save_artifact(
                    project,
                    artifact_key,
                    artifact["payload"],
                    schema_version=schema_version,
                )

            workflow = item.get("workflow")
            if workflow:
                schema_validator.validate_file(
                    workflow,
                    "workflow-state.v1.schema.json",
                )
                runtime = project.runtime
                runtime.metadata = workflow
                runtime.revision = workflow["version"]
                runtime.save(update_fields=["metadata", "revision", "updated_at"])
            imported += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
            self.stdout.write(self.style.WARNING(f"校验通过：{imported} 个项目，未写入"))
        else:
            self.stdout.write(self.style.SUCCESS(f"已导入 {imported} 个项目"))
