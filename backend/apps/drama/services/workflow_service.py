# -*- coding: utf-8 -*-
"""流程状态服务。"""
from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction

from apps.core.audit import audit_log
from apps.core.exceptions import (
    IDEMPOTENCY_CONFLICT,
    OPTIMISTIC_LOCK_FAILED,
    WORKFLOW_GATE_BLOCKED,
    BusinessException,
)
from apps.core.schema_validator import SchemaValidator
from apps.drama.models import DramaAuditEvent, DramaCommand, DramaProject, DramaWorkflowState
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.services.workflow_engine import ConcurrencyError, WorkflowEngine, WorkflowError


class WorkflowService:
    """工作流命令与审批。"""

    SCHEMA_PATH = "workflow-state.v1.schema.json"

    def __init__(self) -> None:
        self.loader = get_skills_loader()
        self.engine = WorkflowEngine(self.loader.workflow_transitions)
        self.validator = SchemaValidator()

    def get_state(self, project: DramaProject) -> dict[str, Any]:
        wf = project.workflow_state
        return wf.state

    @transaction.atomic
    def apply_command(
        self,
        project: DramaProject,
        *,
        command_id: str,
        event: str,
        expected_version: int,
        payload: dict[str, Any] | None = None,
        actor: str,
    ) -> dict[str, Any]:
        existing = DramaCommand.objects.filter(
            project=project, command_id=command_id
        ).first()
        if existing:
            if existing.event != event:
                raise BusinessException(
                    IDEMPOTENCY_CONFLICT,
                    "命令 ID 已被不同事件占用",
                    http_status=409,
                )
            if existing.status == DramaCommand.Status.COMPLETED:
                return existing.response_snapshot or self.get_state(project)

        wf = DramaWorkflowState.objects.select_for_update().get(project=project)
        user_decisions = self.engine.transitions.get("user_decisions") or {}
        try:
            if event in user_decisions:
                new_state = self.engine.decide(
                    wf.state,
                    event,
                    command_id,
                    expected_version,
                )
            else:
                new_state = self.engine.apply(
                    wf.state,
                    event,
                    command_id,
                    expected_version,
                    payload,
                )
        except ConcurrencyError as exc:
            raise BusinessException(
                OPTIMISTIC_LOCK_FAILED,
                str(exc),
                http_status=409,
            ) from exc
        except WorkflowError as exc:
            raise BusinessException(
                WORKFLOW_GATE_BLOCKED,
                str(exc),
                http_status=422,
            ) from exc

        return self._persist_state(
            project,
            wf,
            new_state,
            command_id=command_id,
            event=event,
            payload=payload,
            actor=actor,
        )

    @transaction.atomic
    def approve_story_bible(
        self,
        project: DramaProject,
        *,
        command_id: str,
        decision: str,
        expected_version: int,
        actor: str,
    ) -> dict[str, Any]:
        event = "story_bible_approved" if decision == "approve" else "story_bible_rejected"
        return self.apply_command(
            project,
            command_id=command_id,
            event=event,
            expected_version=expected_version,
            actor=actor,
        )

    @transaction.atomic
    def invalidate_downstream(
        self,
        project: DramaProject,
        *,
        actor: str,
    ) -> dict[str, Any]:
        wf = DramaWorkflowState.objects.select_for_update().get(project=project)
        command_id = f"invalidate-{project.settings_revision}"
        if command_id in wf.state.get("processed_commands", []):
            return wf.state
        new_state = self.engine.apply(
            wf.state,
            "story_bible_changed",
            command_id,
            wf.version,
        )
        return self._persist_state(
            project,
            wf,
            new_state,
            command_id=command_id,
            event="story_bible_changed",
            payload={},
            actor=actor,
        )

    def _persist_state(
        self,
        project: DramaProject,
        wf: DramaWorkflowState,
        new_state: dict[str, Any],
        *,
        command_id: str,
        event: str,
        payload: dict[str, Any] | None,
        actor: str,
    ) -> dict[str, Any]:
        self.validator.validate_file(new_state, self.SCHEMA_PATH)
        wf.state = new_state
        wf.version = new_state["version"]
        wf.save(update_fields=["state", "version", "updated_at"])

        DramaCommand.objects.update_or_create(
            project=project,
            command_id=command_id,
            defaults={
                "event": event,
                "payload": payload or {},
                "status": DramaCommand.Status.COMPLETED,
                "response_snapshot": new_state,
            },
        )
        DramaAuditEvent.objects.create(
            project=project,
            actor=actor,
            action=f"workflow.{event}",
            detail={"command_id": command_id, "version": wf.version},
        )
        audit_log(f"workflow.{event}", actor=actor, project_id=str(project.id))
        return new_state
