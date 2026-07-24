# -*- coding: utf-8 -*-
"""产物版本服务。"""
from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.core.schema_validator import SchemaValidator
from apps.drama.models import DramaArtifactVersion, DramaProject
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.services.script_resolver import resolve_latest_script


SENSITIVE_KEYS = {"api_key", "secret", "password", "token"}


class ArtifactService:
    """产物读写与 latest_script 解析。"""

    def __init__(self) -> None:
        self.loader = get_skills_loader()
        self.validator = SchemaValidator()

    def get_artifact(
        self,
        project: DramaProject,
        artifact_key: str,
        *,
        version: int | None = None,
    ) -> dict[str, Any]:
        qs = DramaArtifactVersion.objects.filter(
            project=project, artifact_key=artifact_key
        )
        if version is not None:
            record = qs.filter(version=version).first()
        else:
            record = qs.order_by("-version").first()
        if record is None:
            return {"artifact_key": artifact_key, "version": None, "payload": None}
        payload = self._redact(record.payload)
        return {
            "artifact_key": artifact_key,
            "version": record.version,
            "schema_version": record.schema_version,
            "payload": payload,
        }

    def latest_script(
        self,
        project: DramaProject,
        episode_range: str | None = None,
    ) -> dict[str, Any]:
        artifacts = self._artifacts_map(project)
        return resolve_latest_script(artifacts, episode_range)

    @transaction.atomic
    def save_artifact(
        self,
        project: DramaProject,
        artifact_key: str,
        payload: dict[str, Any],
        *,
        schema_version: int | None = None,
    ) -> DramaArtifactVersion:
        contract = self.loader.get_artifact_contract(artifact_key)
        schema_path = contract.get("schema_path")
        if schema_path:
            self.validator.validate_file(payload, schema_path)

        if schema_version is not None:
            resolved_version = schema_version
        elif isinstance(contract.get("schema_version"), int):
            resolved_version = contract["schema_version"]
        else:
            raise ValueError(f"产物 {artifact_key} 缺少 schema_version")

        latest = (
            DramaArtifactVersion.objects.select_for_update()
            .filter(project=project, artifact_key=artifact_key)
            .order_by("-version")
            .first()
        )
        next_version = (latest.version + 1) if latest else 1
        record = DramaArtifactVersion.objects.create(
            project=project,
            artifact_key=artifact_key,
            version=next_version,
            schema_version=resolved_version,
            payload=payload,
        )
        return record

    def _artifacts_map(self, project: DramaProject) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for record in (
            DramaArtifactVersion.objects.filter(project=project)
            .order_by("artifact_key", "-version")
            .distinct("artifact_key")
        ):
            result[record.artifact_key] = record.payload
        return result

    def _redact(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                key: ("***" if key in SENSITIVE_KEYS else self._redact(value))
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [self._redact(item) for item in data]
        return data
