# -*- coding: utf-8 -*-
"""生成任务启动门禁与角色/产物映射。"""
from __future__ import annotations

from typing import Any

from apps.core.exceptions import (
    IDEMPOTENCY_CONFLICT,
    OPTIMISTIC_LOCK_FAILED,
    WORKFLOW_GATE_BLOCKED,
    BusinessException,
)
from apps.drama.models import DramaGenerationJob, DramaProject
from apps.drama.services.artifact_service import ArtifactService
from apps.drama.services.skills_loader import SkillsBundleLoader, get_skills_loader

ROLE_COMPLETION_EVENT: dict[str, str] = {
    "drama.topic-director": "project_brief_completed",
    "drama.story-bible": "story_bible_completed",
    "drama.episode-designer": "narrative_plan_completed",
    "drama.script-writer": "episode_batch_completed",
    "drama.revision-master": "polished_script_completed",
    "drama.delivery-tool": "production_package_completed",
}

QUALITY_TRIGGER_ROLES = frozenset({"drama.script-writer", "drama.revision-master"})


class GenerationGate:
    """校验生成启动条件与幂等。"""

    def __init__(self, loader: SkillsBundleLoader | None = None) -> None:
        self.loader = loader or get_skills_loader()
        self.artifacts = ArtifactService()

    def find_idempotent_job(
        self,
        project: DramaProject,
        command_id: str,
        *,
        role: str,
        expected_version: int,
    ) -> DramaGenerationJob | None:
        existing = DramaGenerationJob.objects.filter(
            project=project,
            command_id=command_id,
        ).first()
        if existing is None:
            return None
        payload = existing.request_payload or {}
        if payload.get("role") != role or payload.get("expected_version") != expected_version:
            raise BusinessException(
                IDEMPOTENCY_CONFLICT,
                "命令 ID 已被不同参数占用",
                http_status=409,
            )
        return existing

    def validate_start(
        self,
        project: DramaProject,
        *,
        role: str,
        command_id: str,
        expected_version: int,
    ) -> str:
        wf = project.workflow_state
        if wf.version != expected_version:
            raise BusinessException(
                OPTIMISTIC_LOCK_FAILED,
                f"工作流版本冲突，期望 {expected_version}，实际 {wf.version}",
                http_status=409,
            )

        state = wf.state
        entry_type = state.get("entry_type") or project.settings.get("entry_type", "original_track")
        phase = state.get("current_phase", "")
        track = self.loader.get_orchestration_track(entry_type)

        if not self._role_allowed(track, phase, role, entry_type):
            raise BusinessException(
                WORKFLOW_GATE_BLOCKED,
                f"角色 {role} 不允许在阶段 {phase} 执行",
                http_status=422,
            )

        phase_cfg = self._phase_config(track, phase)
        if phase_cfg:
            for artifact_key in phase_cfg.get("requires_artifacts", []):
                stored = self.artifacts.get_artifact(project, artifact_key)
                if stored.get("payload") is None:
                    raise BusinessException(
                        WORKFLOW_GATE_BLOCKED,
                        f"缺少前置产物: {artifact_key}",
                        http_status=422,
                    )
            for approval in phase_cfg.get("requires_approvals", []):
                if not state.get("approvals", {}).get(approval):
                    raise BusinessException(
                        WORKFLOW_GATE_BLOCKED,
                        f"缺少审批: {approval}",
                        http_status=422,
                    )

        if (
            entry_type == "story_adapt"
            and phase == "blueprint"
            and role == "drama.story-bible"
        ):
            external = (project.settings.get("external_story") or "").strip()
            if not external:
                raise BusinessException(
                    WORKFLOW_GATE_BLOCKED,
                    "故事改编通道需要填写 external_story 后才能执行蓝图",
                    http_status=422,
                )

        contract = self.loader.get_role_contract(role)
        return contract.get("default_output_artifact_key", "")

    def completion_event_for_role(self, role: str) -> str:
        event = ROLE_COMPLETION_EVENT.get(role)
        if not event:
            raise BusinessException(
                WORKFLOW_GATE_BLOCKED,
                f"角色 {role} 无对应完成事件",
                http_status=422,
            )
        return event

    def _role_allowed(
        self,
        track: dict[str, Any],
        phase: str,
        role: str,
        entry_type: str,
    ) -> bool:
        if phase == "revision" and role == "drama.revision-master":
            return True
        if phase == "delivery" and role == "drama.delivery-tool":
            return True
        phase_cfg = self._phase_config(track, phase)
        if phase_cfg is None:
            return False
        return role in (phase_cfg.get("agents") or [])

    def _phase_config(
        self, track: dict[str, Any], phase: str
    ) -> dict[str, Any] | None:
        for item in track.get("phases", []):
            if item.get("phase") == phase:
                return item
        return None
