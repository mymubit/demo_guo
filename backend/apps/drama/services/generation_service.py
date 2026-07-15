# -*- coding: utf-8 -*-
"""异步生成任务编排。"""
from __future__ import annotations

import json
import logging
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.exceptions import BusinessException
from apps.core.schema_validator import SchemaValidator
from apps.drama.models import DramaGenerationJob, DramaProject
from apps.drama.services.artifact_service import ArtifactService
from apps.drama.services.generation_gate import QUALITY_TRIGGER_ROLES, GenerationGate
from apps.drama.services.json_parse import JsonParseError, parse_and_validate
from apps.drama.services.llm_provider import LlmProvider, LlmProviderError, LlmProviderStatus
from apps.drama.services.prompt_builder import PromptBuilder
from apps.drama.services.quality_gate import quality_gate_passed
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)

TERMINAL_JOB_STATUSES = frozenset(
    {
        DramaGenerationJob.Status.COMPLETED,
        DramaGenerationJob.Status.FAILED,
        DramaGenerationJob.Status.DISABLED,
    }
)


class GenerationService:
    """GenerationJob 生命周期管理。"""

    def __init__(self) -> None:
        self.loader = get_skills_loader()
        self.gate = GenerationGate(self.loader)
        self.prompts = PromptBuilder(self.loader)
        self.artifacts = ArtifactService()
        self.workflow = WorkflowService()
        self.validator = SchemaValidator()

    def start_generation(
        self,
        project: DramaProject,
        *,
        command_id: str,
        expected_version: int,
        role: str,
        input_payload: dict[str, Any],
        actor: str,
    ) -> DramaGenerationJob:
        existing = self.gate.find_idempotent_job(
            project,
            command_id,
            role=role,
            expected_version=expected_version,
        )
        if existing is not None:
            return existing

        artifact_key = self.gate.validate_start(
            project,
            role=role,
            command_id=command_id,
            expected_version=expected_version,
        )
        project.refresh_from_db()
        wf_version = project.workflow_state.version

        try:
            job = DramaGenerationJob.objects.create(
                project=project,
                job_type=DramaGenerationJob.JobType.GENERATION,
                status=DramaGenerationJob.Status.QUEUED,
                command_id=command_id,
                role=role,
                artifact_key=artifact_key,
                workflow_version=wf_version,
                request_payload={
                    "command_id": command_id,
                    "expected_version": expected_version,
                    "role": role,
                    "input": input_payload,
                    "actor": actor,
                },
            )
        except IntegrityError:
            return self.gate.find_idempotent_job(
                project,
                command_id,
                role=role,
                expected_version=expected_version,
            )

        from apps.drama.tasks import run_generation_task

        async_result = run_generation_task.delay(str(job.id))
        job.celery_task_id = async_result.id
        job.save(update_fields=["celery_task_id", "updated_at"])
        return job

    def start_external_review(
        self,
        *,
        command_id: str,
        script_content: str,
        scoring_preset: str,
        check_mode: str,
        actor: str,
        owner: AbstractBaseUser,
        project: DramaProject | None = None,
    ) -> DramaGenerationJob:
        if project is not None:
            existing = DramaGenerationJob.objects.filter(
                project=project,
                command_id=command_id,
            ).first()
            if existing is not None:
                return existing
        else:
            existing = DramaGenerationJob.objects.filter(
                owner=owner,
                project__isnull=True,
                command_id=command_id,
            ).first()
            if existing is not None:
                payload = existing.request_payload or {}
                if payload.get("actor") != actor:
                    from apps.core.exceptions import IDEMPOTENCY_CONFLICT, BusinessException

                    raise BusinessException(
                        IDEMPOTENCY_CONFLICT,
                        "命令 ID 已被不同操作人占用",
                        http_status=409,
                    )
                return existing

        try:
            job = DramaGenerationJob.objects.create(
                project=project,
                owner=owner if project is None else None,
                job_type=DramaGenerationJob.JobType.EXTERNAL_REVIEW,
                status=DramaGenerationJob.Status.QUEUED,
                command_id=command_id,
                role="drama.script-scorer+drama.compliance-guard",
                artifact_key="quality_report+compliance_report",
                request_payload={
                    "command_id": command_id,
                    "script_content": script_content,
                    "scoring_preset": scoring_preset,
                    "check_mode": check_mode,
                    "actor": actor,
                    "scoring_mode": "external",
                },
            )
        except IntegrityError:
            if project is not None:
                return DramaGenerationJob.objects.get(
                    project=project,
                    command_id=command_id,
                )
            return DramaGenerationJob.objects.get(
                owner=owner,
                project__isnull=True,
                command_id=command_id,
            )

        from apps.drama.tasks import run_external_review_task

        async_result = run_external_review_task.delay(str(job.id))
        job.celery_task_id = async_result.id
        job.save(update_fields=["celery_task_id", "updated_at"])
        return job

    def get_job(self, job_id: str) -> DramaGenerationJob:
        return DramaGenerationJob.objects.get(id=job_id)

    def get_status(self, job: DramaGenerationJob) -> dict[str, Any]:
        return {
            "job_id": str(job.id),
            "job_type": job.job_type,
            "status": job.status,
            "result": job.result_payload,
            "error": job.error_message or None,
            "progress_events": job.progress_events,
            "celery_task_id": job.celery_task_id,
            "llm_status": LlmProvider.status().value,
        }

    @transaction.atomic
    def append_progress(self, job: DramaGenerationJob, event: dict[str, Any]) -> None:
        locked = DramaGenerationJob.objects.select_for_update().get(pk=job.pk)
        events = list(locked.progress_events or [])
        event["ts"] = timezone.now().isoformat()
        events.append(event)
        locked.progress_events = events
        locked.save(update_fields=["progress_events", "updated_at"])
        job.progress_events = locked.progress_events

    @transaction.atomic
    def mark_running(self, job: DramaGenerationJob) -> None:
        locked = DramaGenerationJob.objects.select_for_update().get(pk=job.pk)
        locked.status = DramaGenerationJob.Status.RUNNING
        locked.save(update_fields=["status", "updated_at"])
        job.status = locked.status

    @transaction.atomic
    def mark_completed(
        self, job: DramaGenerationJob, result: dict[str, Any]
    ) -> None:
        locked = DramaGenerationJob.objects.select_for_update().get(pk=job.pk)
        locked.status = DramaGenerationJob.Status.COMPLETED
        locked.result_payload = result
        locked.save(update_fields=["status", "result_payload", "updated_at"])
        job.status = locked.status
        job.result_payload = locked.result_payload

    @transaction.atomic
    def mark_failed(self, job: DramaGenerationJob, message: str) -> None:
        locked = DramaGenerationJob.objects.select_for_update().get(pk=job.pk)
        locked.status = DramaGenerationJob.Status.FAILED
        locked.error_message = message
        locked.save(update_fields=["status", "error_message", "updated_at"])
        job.status = locked.status
        job.error_message = locked.error_message

    @transaction.atomic
    def mark_disabled(self, job: DramaGenerationJob, message: str) -> None:
        locked = DramaGenerationJob.objects.select_for_update().get(pk=job.pk)
        locked.status = DramaGenerationJob.Status.DISABLED
        locked.error_message = message
        locked.save(update_fields=["status", "error_message", "updated_at"])
        job.status = locked.status
        job.error_message = locked.error_message

    def mark_failed_if_active(self, job_id: str, message: str) -> None:
        with transaction.atomic():
            locked = DramaGenerationJob.objects.select_for_update().get(pk=job_id)
            if locked.status in TERMINAL_JOB_STATUSES:
                return
            locked.status = DramaGenerationJob.Status.FAILED
            locked.error_message = message
            locked.save(update_fields=["status", "error_message", "updated_at"])

    def execute_generation(self, job_id: str) -> None:
        """Celery worker 执行入口。"""
        job = self.get_job(job_id)
        if job.status in TERMINAL_JOB_STATUSES:
            return

        self.mark_running(job)
        self.append_progress(job, {"phase": "started", "message": "任务开始"})

        llm_status = LlmProvider.status()
        if llm_status == LlmProviderStatus.DISABLED:
            self.mark_disabled(job, "LLM 已禁用，任务未执行")
            return
        if llm_status == LlmProviderStatus.MISCONFIGURED:
            self.mark_failed(job, "LLM 配置不完整")
            return

        project = job.project
        payload = job.request_payload
        role = payload.get("role", "")
        try:
            artifact_payload = self._generate_artifact(project, role, payload)
            self._persist_generation_result(job, project, role, payload, artifact_payload)
        except (LlmProviderError, JsonParseError) as exc:
            self.mark_failed(job, str(exc))
        except BusinessException as exc:
            self.mark_failed(job, str(exc))
        except Exception:
            logger.exception("Generation failed for job %s", job_id)
            self.mark_failed(job, "生成失败")
            raise

    def execute_external_review(self, job_id: str) -> None:
        """外部审稿：并行评分与合规。"""
        job = self.get_job(job_id)
        if job.status in TERMINAL_JOB_STATUSES:
            return

        self.mark_running(job)
        payload = job.request_payload

        llm_status = LlmProvider.status()
        if llm_status != LlmProviderStatus.ENABLED:
            self.mark_disabled(
                job,
                f"LLM 不可用 ({llm_status.value})，未冒充成功",
            )
            return

        if job.project_id:
            self._save_external_script(job.project, payload["script_content"])

        from apps.drama.tasks import run_parallel_judge_task

        async_result = run_parallel_judge_task.delay(str(job.id))
        job.celery_task_id = async_result.id
        job.job_type = DramaGenerationJob.JobType.PARALLEL_JUDGE
        job.save(update_fields=["celery_task_id", "job_type", "updated_at"])

    def _generate_artifact(
        self,
        project: DramaProject,
        role: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        settings = project.settings
        wf_state = project.workflow_state.state
        artifacts = self._collect_artifacts(project)
        latest_script = None
        contract = self.loader.get_role_contract(role)
        if "latest_script" in (contract.get("input_contract") or {}).get(
            "required_artifacts", []
        ):
            latest_script = self.artifacts.latest_script(project)

        system_prompt, user_prompt = self.prompts.build(
            role,
            settings=settings,
            workflow_state=wf_state,
            artifacts=artifacts,
            input_payload=payload.get("input"),
            latest_script=latest_script,
        )
        response = LlmProvider.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
        )
        content = response["choices"][0]["message"]["content"]
        artifact_key = self.loader.get_output_artifact_by_role(role)
        schema_path = self.loader.artifact_schema_path(artifact_key)
        return parse_and_validate(
            content,
            validator=self.validator,
            schema_path=schema_path,
        )

    def _workflow_version_for_job(
        self, job: DramaGenerationJob, payload: dict[str, Any]
    ) -> int:
        if job.workflow_version is not None:
            return job.workflow_version
        return int(payload["expected_version"])

    @transaction.atomic
    def _persist_generation_result(
        self,
        job: DramaGenerationJob,
        project: DramaProject,
        role: str,
        payload: dict[str, Any],
        artifact_payload: dict[str, Any],
    ) -> None:
        expected_version = self._workflow_version_for_job(job, payload)
        self.gate.validate_start(
            project,
            role=role,
            command_id=payload["command_id"],
            expected_version=expected_version,
        )

        contract = self.loader.get_role_contract(role)
        artifact_key = self.loader.get_output_artifact_by_role(role)
        self.artifacts.save_artifact(project, artifact_key, artifact_payload)
        self.append_progress(job, {"phase": "artifact_saved", "artifact_key": artifact_key})

        event = self.gate.completion_event_for_role(role)
        command_id = payload["command_id"]
        self.workflow.apply_command(
            project,
            command_id=f"{command_id}-complete",
            event=event,
            expected_version=expected_version,
            payload=None,
            actor=payload.get("actor", "system"),
        )

        result = {
            "artifact_key": artifact_key,
            "artifact_version": self.artifacts.get_artifact(project, artifact_key)["version"],
            "workflow_event": event,
        }
        self.mark_completed(job, result)

        if role in QUALITY_TRIGGER_ROLES:
            self._schedule_quality_chord(job, project, payload)

    def _schedule_quality_chord(
        self,
        job: DramaGenerationJob,
        project: DramaProject,
        payload: dict[str, Any],
    ) -> None:
        from apps.drama.tasks import run_parallel_judge_task

        project.workflow_state.refresh_from_db()
        judge_job = DramaGenerationJob.objects.create(
            project=project,
            job_type=DramaGenerationJob.JobType.PARALLEL_JUDGE,
            status=DramaGenerationJob.Status.QUEUED,
            command_id=f"{payload['command_id']}-quality",
            role="drama.script-scorer+drama.compliance-guard",
            artifact_key="quality_report+compliance_report",
            workflow_version=project.workflow_state.version,
            request_payload={
                **payload,
                "parent_job_id": str(job.id),
                "scoring_mode": "project",
            },
        )
        async_result = run_parallel_judge_task.delay(str(judge_job.id))
        judge_job.celery_task_id = async_result.id
        judge_job.save(update_fields=["celery_task_id", "updated_at"])
        self.append_progress(
            job,
            {"phase": "quality_scheduled", "judge_job_id": str(judge_job.id)},
        )

    def _build_quality_report(
        self, job: DramaGenerationJob, payload: dict[str, Any]
    ) -> dict[str, Any]:
        role = "drama.script-scorer"
        project = job.project
        settings = (project.settings if project else {}) or {}
        if payload.get("scoring_preset"):
            prefs = dict(settings.get("creation_preferences") or {})
            prefs["scoring_preset"] = payload["scoring_preset"]
            settings = {**settings, "creation_preferences": prefs}

        artifacts: dict[str, Any] = {}
        latest_script = None
        if project:
            artifacts = self._collect_artifacts(project)
            latest_script = self.artifacts.latest_script(project)
        elif payload.get("script_content"):
            latest_script = {
                "resolved_script_key": "external_script",
                "value": {"episodes": [{"script": payload["script_content"]}]},
            }

        system_prompt, user_prompt = self.prompts.build(
            role,
            settings=settings,
            workflow_state=project.workflow_state.state if project else {},
            artifacts=artifacts,
            input_payload={"episode_range": payload.get("input", {}).get("episode_range")},
            latest_script=latest_script,
            scoring_mode=payload.get("scoring_mode", "project"),
        )
        response = LlmProvider.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
        )
        content = response["choices"][0]["message"]["content"]
        artifact_key = self.loader.get_output_artifact_by_role(role)
        schema_path = self.loader.artifact_schema_path(artifact_key)
        return parse_and_validate(
            content,
            validator=self.validator,
            schema_path=schema_path,
        )

    def _build_compliance_report(
        self, job: DramaGenerationJob, payload: dict[str, Any]
    ) -> dict[str, Any]:
        role = "drama.compliance-guard"
        project = job.project
        settings = (project.settings if project else {}) or {}
        if payload.get("check_mode"):
            prefs = dict(settings.get("creation_preferences") or {})
            prefs["compliance_check_mode"] = payload["check_mode"]
            settings = {**settings, "creation_preferences": prefs}

        artifacts: dict[str, Any] = {}
        latest_script = None
        if project:
            artifacts = self._collect_artifacts(project)
            latest_script = self.artifacts.latest_script(project)
        elif payload.get("script_content"):
            latest_script = {
                "resolved_script_key": "external_script",
                "value": {"episodes": [{"script": payload["script_content"]}]},
            }

        system_prompt, user_prompt = self.prompts.build(
            role,
            settings=settings,
            workflow_state=project.workflow_state.state if project else {},
            artifacts=artifacts,
            latest_script=latest_script,
            scoring_mode=payload.get("scoring_mode", "external"),
        )
        response = LlmProvider.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
        )
        content = response["choices"][0]["message"]["content"]
        artifact_key = self.loader.get_output_artifact_by_role(role)
        schema_path = self.loader.artifact_schema_path(artifact_key)
        return parse_and_validate(
            content,
            validator=self.validator,
            schema_path=schema_path,
        )

    def _finalize_quality_results(
        self,
        job: DramaGenerationJob,
        score_result: dict[str, Any],
        compliance_result: dict[str, Any],
    ) -> None:
        try:
            with transaction.atomic():
                self._finalize_quality_results_tx(job, score_result, compliance_result)
        except Exception:
            logger.exception("Quality finalize failed for job %s", job.id)
            self.mark_failed_if_active(str(job.id), "质量评审落库失败")
            raise

    @transaction.atomic
    def _finalize_quality_results_tx(
        self,
        job: DramaGenerationJob,
        score_result: dict[str, Any],
        compliance_result: dict[str, Any],
    ) -> None:
        payload = job.request_payload
        project = job.project
        command_id = payload["command_id"]

        self.append_progress(job, {"phase": "scoring_done"})
        self.append_progress(job, {"phase": "compliance_done"})

        if project:
            expected_version = self._workflow_version_for_job(job, payload)
            self.artifacts.save_artifact(project, "quality_report", score_result)
            self.artifacts.save_artifact(project, "compliance_report", compliance_result)

            self.workflow.apply_command(
                project,
                command_id=f"{command_id}-score",
                event="quality_score_completed",
                expected_version=expected_version,
                payload=score_result,
                actor=payload.get("actor", "system"),
            )
            project.workflow_state.refresh_from_db()
            self.workflow.apply_command(
                project,
                command_id=f"{command_id}-compliance",
                event="compliance_completed",
                expected_version=project.workflow_state.version,
                payload=compliance_result,
                actor=payload.get("actor", "system"),
            )
            project.workflow_state.refresh_from_db()
            passed = quality_gate_passed(score_result, compliance_result)
            gate_event = "quality_passed" if passed else "quality_failed"
            self.workflow.apply_command(
                project,
                command_id=f"{command_id}-gate",
                event=gate_event,
                expected_version=project.workflow_state.version,
                payload={
                    "overall_score": score_result.get("overall_score"),
                    "blocking_issues": compliance_result.get("blocking_issues", []),
                },
                actor=payload.get("actor", "system"),
            )

        self.mark_completed(
            job,
            {
                "quality_report": score_result,
                "compliance_report": compliance_result,
                "quality_passed": quality_gate_passed(score_result, compliance_result),
            },
        )

    def _collect_artifacts(self, project: DramaProject) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key in self.loader.artifacts_contract.get("artifacts", {}):
            stored = self.artifacts.get_artifact(project, key)
            if stored.get("payload") is not None:
                result[key] = stored["payload"]
        return result

    def _save_external_script(self, project: DramaProject, script_content: str) -> None:
        payload = {
            "episodes": [
                {
                    "episode_number": 1,
                    "title": "外部投稿",
                    "script": script_content,
                    "word_count": len(script_content),
                    "dialogue_ratio": 0.4,
                    "scene_count": 1,
                    "golden_lines": [],
                    "format_check": {},
                    "memory_checkpoint": {
                        "episode": 1,
                        "character_states": [],
                        "active_clues": [],
                        "foreshadowing": [],
                        "relationship_changes": [],
                        "prop_states": [],
                        "rhythm_state": {
                            "plot_pace": "tight",
                            "emotion_pace": "heavy",
                            "episode_ev": 5,
                            "episode_et": 3,
                            "episode_tp": "",
                        },
                        "next_episode_constraints": [],
                    },
                    "production_notes": {
                        "tags": [],
                        "complexity_score": 0,
                        "complexity_band": "lean",
                        "high_cost_scenes": [],
                        "lower_cost_alternatives": [],
                    },
                }
            ]
        }
        episode_contract = self.loader.get_artifact_contract("episode_scripts")
        self.validator.validate_file(payload, episode_contract["schema_path"])
        self.artifacts.save_artifact(
            project,
            "external_script",
            payload,
            schema_version=episode_contract["schema_version"],
        )
