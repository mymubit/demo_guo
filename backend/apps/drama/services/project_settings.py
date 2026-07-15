# -*- coding: utf-8 -*-
"""项目设置派生与持久化。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction

from apps.core.audit import audit_log
from apps.core.exceptions import (
    OPTIMISTIC_LOCK_FAILED,
    BusinessException,
)
from apps.core.schema_validator import SchemaValidator
from apps.drama.models import DramaAuditEvent, DramaProject, DramaWorkflowState
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.services.workflow_engine import WorkflowEngine
from apps.drama.services.workflow_service import WorkflowService


class ProjectSettingsService:
    """项目设置 CRUD 与派生字段计算。"""

    def __init__(self) -> None:
        self.validator = SchemaValidator()
        self.loader = get_skills_loader()

    @property
    def schema_path(self) -> str:
        path = self.loader.project_settings_schema_path
        if path.startswith("schemas/"):
            return path[len("schemas/") :]
        return path

    def default_settings(
        self,
        project: DramaProject,
        *,
        entry_type: str = "original_track",
        actor: str,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        settings: dict[str, Any] = {
            "schema_version": "project-settings.v1",
            "project_id": str(project.id),
            "skills_version": self.loader.bundle_version,
            "entry_type": entry_type,
            "title": project.title,
            "core_idea": "",
            "production_context": {},
            "platform_policy": {
                "policy_version": None,
                "policy_source": None,
                "verified_at": None,
            },
            "audit": {
                "revision": 1,
                "created_at": now,
                "updated_at": now,
                "updated_by": actor,
            },
        }
        settings = self.loader.apply_parameter_defaults(settings)
        return self._derive(settings)

    @transaction.atomic
    def create_project(
        self,
        owner: AbstractBaseUser,
        title: str,
        *,
        entry_type: str = "original_track",
        episode_count: int | None = None,
        core_idea: str | None = None,
        external_story: str | None = None,
    ) -> DramaProject:
        project = DramaProject.objects.create(
            owner=owner,
            title=title,
            skills_version=self.loader.bundle_version,
        )
        settings = self.default_settings(
            project,
            entry_type=entry_type,
            actor=owner.username,
        )
        if episode_count is not None:
            settings["episode_count"] = episode_count
        if entry_type == "original_track":
            settings["core_idea"] = core_idea if core_idea is not None else title
        elif core_idea:
            settings["core_idea"] = core_idea
        if external_story is not None:
            settings["external_story"] = external_story
        project.settings = settings
        project.save(update_fields=["settings", "skills_version", "updated_at"])

        engine = WorkflowEngine(self.loader.workflow_transitions)
        state = engine.create(str(project.id), entry_type)
        DramaWorkflowState.objects.create(project=project, state=state, version=0)

        DramaAuditEvent.objects.create(
            project=project,
            actor=owner.username,
            action="project.created",
            detail={"title": title, "entry_type": entry_type},
        )
        audit_log("project.created", actor=owner, project_id=str(project.id))
        return project

    def get_settings(self, project: DramaProject) -> dict[str, Any]:
        return project.settings

    @transaction.atomic
    def update_settings(
        self,
        project: DramaProject,
        payload: dict[str, Any],
        *,
        expected_revision: int,
        actor: str,
    ) -> dict[str, Any]:
        if project.settings_revision != expected_revision:
            raise BusinessException(
                OPTIMISTIC_LOCK_FAILED,
                f"设置版本冲突，期望 {expected_revision}，实际 {project.settings_revision}",
                http_status=409,
            )

        payload = dict(payload)
        payload["project_id"] = str(project.id)
        payload["skills_version"] = self.loader.bundle_version
        payload = self.loader.apply_parameter_defaults(payload)
        derived = self._derive(payload)
        self.validator.validate_file(derived, self.schema_path)

        old_settings = project.settings
        blueprint_changed = self._blueprint_inputs_changed(old_settings, derived)

        now = datetime.now(timezone.utc).isoformat()
        audit = derived.get("audit", {})
        audit["revision"] = expected_revision + 1
        audit["updated_at"] = now
        audit["updated_by"] = actor
        audit.setdefault("created_at", old_settings.get("audit", {}).get("created_at", now))
        derived["audit"] = audit

        project.settings = derived
        project.settings_revision = expected_revision + 1
        project.title = derived.get("title") or project.title
        project.save(update_fields=["settings", "settings_revision", "title", "updated_at"])

        if blueprint_changed:
            WorkflowService().invalidate_downstream(project, actor=actor)

        DramaAuditEvent.objects.create(
            project=project,
            actor=actor,
            action="project.settings_updated",
            detail={"revision": project.settings_revision},
        )
        return derived

    def _derive(self, settings: dict[str, Any]) -> dict[str, Any]:
        result = dict(settings)
        matrix = result.get("genre_matrix") or {}
        if matrix:
            key = "-".join(
                matrix.get(axis, "")
                for axis in ("emotion", "identity", "conflict", "world")
            )
            result["derived"] = {
                "matrix_key": key,
                "rule_params_ref": "project_brief.rule_params",
            }
        platform = result.get("target_platform", "generic")
        profiles = self.loader.load_seed_yaml(
            "foundation/constraints/platform-profiles.yaml"
        ).get("platforms", {})
        profile = profiles.get(platform, {})
        result["platform_policy"] = {
            "policy_version": profile.get("policy_version"),
            "policy_source": profile.get("policy_source"),
            "verified_at": profile.get("verified_at"),
        }
        return result

    def _blueprint_inputs_changed(
        self, old: dict[str, Any], new: dict[str, Any]
    ) -> bool:
        keys = (
            "core_idea",
            "external_story",
            "genre_matrix",
            "episode_count",
            "adapt_notes",
        )
        return any(old.get(k) != new.get(k) for k in keys)
