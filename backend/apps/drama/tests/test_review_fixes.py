# -*- coding: utf-8 -*-
"""审查修复回归测试。"""
from __future__ import annotations

import importlib
import json
import os
import threading
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase, override_settings

from apps.core.exceptions import CONFIG_OVERLAY_FORBIDDEN, IDEMPOTENCY_CONFLICT
from apps.drama.job_payload import sse_heartbeat_event, sse_terminal_event, sse_timeout_event
from apps.drama.models import DramaArtifactVersion, DramaGenerationJob
from apps.drama.services.config_overlay import ConfigOverlayService
from apps.drama.services.generation_service import GenerationService, TERMINAL_JOB_STATUSES
from apps.drama.tasks import _parallel_judge_callback, _score_subtask, run_parallel_judge_task
from apps.drama.tests.helpers import FIXTURES, SKILLS_ROOT, auth_client, create_project, create_user


def _mock_llm_response(payload: dict) -> dict:
    return {
        "choices": [
            {"message": {"content": json.dumps(payload, ensure_ascii=False)}}
        ]
    }


class CeleryTestSettingsTests(TestCase):
    def test_celery_always_eager_reads_env_default_true(self):
        os.environ.pop("CELERY_TASK_ALWAYS_EAGER", None)
        mod = importlib.import_module("config.settings.test")
        importlib.reload(mod)
        self.assertTrue(mod.CELERY_TASK_ALWAYS_EAGER)

    def test_celery_always_eager_reads_env_false(self):
        os.environ["CELERY_TASK_ALWAYS_EAGER"] = "false"
        mod = importlib.import_module("config.settings.test")
        importlib.reload(mod)
        self.assertFalse(mod.CELERY_TASK_ALWAYS_EAGER)
        os.environ.pop("CELERY_TASK_ALWAYS_EAGER", None)
        importlib.reload(mod)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    LLM_ENABLED=False,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class StartGenerationIntegrityTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.project = create_project(self.user)
        self.svc = GenerationService()

    def test_integrity_error_revalidates_matching_job(self):
        existing = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.QUEUED,
            command_id="race-1",
            role="drama.topic-director",
            workflow_version=0,
            request_payload={
                "role": "drama.topic-director",
                "expected_version": 0,
            },
        )
        with patch(
            "apps.drama.models.DramaGenerationJob.objects.create",
            side_effect=IntegrityError("dup"),
        ):
            job = self.svc.start_generation(
                self.project,
                command_id="race-1",
                expected_version=0,
                role="drama.topic-director",
                input_payload={},
                actor=self.user.username,
            )
        self.assertEqual(job.id, existing.id)

    def test_integrity_error_rejects_role_mismatch(self):
        DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.QUEUED,
            command_id="race-2",
            role="drama.topic-director",
            request_payload={
                "role": "drama.topic-director",
                "expected_version": 0,
            },
        )
        from apps.core.exceptions import BusinessException

        with patch(
            "apps.drama.models.DramaGenerationJob.objects.create",
            side_effect=IntegrityError("dup"),
        ):
            with self.assertRaises(BusinessException) as ctx:
                self.svc.start_generation(
                    self.project,
                    command_id="race-2",
                    expected_version=0,
                    role="drama.story-bible",
                    input_payload={},
                    actor=self.user.username,
                )
        self.assertEqual(ctx.exception.code, IDEMPOTENCY_CONFLICT)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    LLM_ENABLED=False,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class ExternalReviewIdempotencyTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.other = create_user(username="other-user")
        self.project = create_project(self.user)
        self.svc = GenerationService()

    def test_orphan_review_idempotent_by_owner_and_command(self):
        first = self.svc.start_external_review(
            command_id="ext-idem",
            script_content="剧本A",
            scoring_preset="standard",
            check_mode="standard",
            actor=self.user.username,
            owner=self.user,
        )
        second = self.svc.start_external_review(
            command_id="ext-idem",
            script_content="剧本B",
            scoring_preset="standard",
            check_mode="standard",
            actor=self.user.username,
            owner=self.user,
        )
        self.assertEqual(first.id, second.id)
        self.assertEqual(first.owner_id, self.user.id)

    def test_orphan_review_allows_different_owners_same_command(self):
        first = self.svc.start_external_review(
            command_id="ext-shared",
            script_content="剧本",
            scoring_preset="standard",
            check_mode="standard",
            actor=self.user.username,
            owner=self.user,
        )
        second = self.svc.start_external_review(
            command_id="ext-shared",
            script_content="剧本",
            scoring_preset="standard",
            check_mode="standard",
            actor=self.other.username,
            owner=self.other,
        )
        self.assertNotEqual(first.id, second.id)

    def test_project_review_allows_concurrent_distinct_commands(self):
        first = self.svc.start_external_review(
            command_id="proj-ext-1",
            script_content="剧本1",
            scoring_preset="standard",
            check_mode="standard",
            actor=self.user.username,
            owner=self.user,
            project=self.project,
        )
        second = self.svc.start_external_review(
            command_id="proj-ext-2",
            script_content="剧本2",
            scoring_preset="standard",
            check_mode="standard",
            actor=self.user.username,
            owner=self.user,
            project=self.project,
        )
        self.assertNotEqual(first.id, second.id)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    LLM_ENABLED=True,
    LLM_API_BASE_URL="http://test",
    LLM_API_KEY="k",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class ParallelJudgeTaskTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.svc = GenerationService()

    @patch("apps.drama.services.generation_service.LlmProvider.chat_completion")
    def test_parallel_judge_marks_running_on_entry(self, mock_llm):
        def side_effect(**kwargs):
            prompt = kwargs.get("system_prompt", "")
            if "合规" in prompt or "compliance" in prompt:
                return _mock_llm_response(FIXTURES["compliance_report"])
            return _mock_llm_response(FIXTURES["quality_report"])

        mock_llm.side_effect = side_effect
        job = DramaGenerationJob.objects.create(
            job_type=DramaGenerationJob.JobType.PARALLEL_JUDGE,
            status=DramaGenerationJob.Status.QUEUED,
            command_id="pj-run",
            owner=self.user,
            request_payload={
                "command_id": "pj-run",
                "script_content": "测试",
                "scoring_mode": "external",
                "actor": self.user.username,
            },
        )
        run_parallel_judge_task(str(job.id))
        job.refresh_from_db()
        self.assertNotEqual(job.status, DramaGenerationJob.Status.QUEUED)
        self.assertIn(job.status, TERMINAL_JOB_STATUSES)

    def test_subtask_failure_marks_job_failed(self):
        job = DramaGenerationJob.objects.create(
            job_type=DramaGenerationJob.JobType.PARALLEL_JUDGE,
            status=DramaGenerationJob.Status.RUNNING,
            command_id="pj-fail",
            owner=self.user,
            request_payload={
                "command_id": "pj-fail",
                "script_content": "测试",
                "scoring_mode": "external",
                "actor": self.user.username,
            },
        )
        with patch.object(
            GenerationService,
            "_build_quality_report",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(RuntimeError):
                _score_subtask(str(job.id))
        job.refresh_from_db()
        self.assertEqual(job.status, DramaGenerationJob.Status.FAILED)

    def test_callback_failure_marks_job_failed(self):
        job = DramaGenerationJob.objects.create(
            job_type=DramaGenerationJob.JobType.PARALLEL_JUDGE,
            status=DramaGenerationJob.Status.RUNNING,
            command_id="pj-cb",
            owner=self.user,
            request_payload={"command_id": "pj-cb", "actor": self.user.username},
        )
        with patch.object(
            GenerationService,
            "_finalize_quality_results",
            side_effect=RuntimeError("finalize boom"),
        ):
            with self.assertRaises(RuntimeError):
                _parallel_judge_callback(
                    [FIXTURES["quality_report"], FIXTURES["compliance_report"]],
                    str(job.id),
                )
        job.refresh_from_db()
        self.assertEqual(job.status, DramaGenerationJob.Status.FAILED)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    LLM_ENABLED=True,
    LLM_API_BASE_URL="http://test",
    LLM_API_KEY="k",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class GenerationTerminalAndVersionTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.project = create_project(self.user)
        self.svc = GenerationService()

    @patch("apps.drama.services.generation_service.LlmProvider.chat_completion")
    def test_terminal_job_skips_llm_on_retry(self, mock_llm):
        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.COMPLETED,
            command_id="done-1",
            role="drama.topic-director",
            workflow_version=0,
            request_payload={
                "command_id": "done-1",
                "expected_version": 0,
                "role": "drama.topic-director",
                "actor": self.user.username,
            },
        )
        self.svc.execute_generation(str(job.id))
        mock_llm.assert_not_called()

    @patch("apps.drama.services.generation_service.LlmProvider.chat_completion")
    def test_persist_uses_captured_workflow_version(self, mock_llm):
        mock_llm.return_value = _mock_llm_response(FIXTURES["project_brief"])
        self.project.workflow_state.version = 5
        self.project.workflow_state.save(update_fields=["version"])
        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.QUEUED,
            command_id="stale-ver",
            role="drama.topic-director",
            artifact_key="project_brief",
            workflow_version=0,
            request_payload={
                "command_id": "stale-ver",
                "expected_version": 0,
                "role": "drama.topic-director",
                "input": {},
                "actor": self.user.username,
            },
        )
        self.svc.execute_generation(str(job.id))
        job.refresh_from_db()
        self.assertEqual(job.status, DramaGenerationJob.Status.FAILED)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    LLM_ENABLED=False,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class QualityFinalizeAtomicTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.project = create_project(self.user)
        self.svc = GenerationService()

    def test_finalize_rolls_back_artifacts_on_workflow_failure(self):
        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.PARALLEL_JUDGE,
            status=DramaGenerationJob.Status.RUNNING,
            command_id="qf-atomic",
            workflow_version=0,
            request_payload={
                "command_id": "qf-atomic",
                "actor": self.user.username,
            },
        )
        with patch.object(
            GenerationService,
            "_workflow_version_for_job",
            return_value=999,
        ):
            with self.assertRaises(Exception):
                self.svc._finalize_quality_results(
                    job,
                    FIXTURES["quality_report"],
                    FIXTURES["compliance_report"],
                )
        job.refresh_from_db()
        self.assertEqual(job.status, DramaGenerationJob.Status.FAILED)
        self.assertFalse(
            DramaArtifactVersion.objects.filter(
                project=self.project, artifact_key="quality_report"
            ).exists()
        )


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class ConfigRollbackValidationTests(TestCase):
    def setUp(self):
        self.svc = ConfigOverlayService()
        self.base_overlay = {
            "schema_version": "ops-config-overlay.v1",
            "tenant_id": "test",
            "skills_version": "5.0.0",
            "overrides": {
                "foundation/constraints/quality-scoring.yaml": {
                    "grade_thresholds": {"B": 78}
                }
            },
            "audit": {
                "revision": 1,
                "updated_by": "admin",
                "updated_at": "2026-07-14T00:00:00Z",
                "change_reason": "测试",
            },
        }

    def test_rollback_revalidates_schema_and_policy(self):
        self.svc.put_overlay(self.base_overlay, expected_revision=0, actor="admin")
        rolled = self.svc.rollback(
            target_revision=1,
            change_reason="回滚",
            actor="admin",
        )
        self.assertEqual(rolled["audit"]["revision"], 2)

    def test_rollback_rejects_forbidden_overlay(self):
        from apps.core.exceptions import BusinessException

        self.svc.put_overlay(self.base_overlay, expected_revision=0, actor="admin")
        bad = dict(self.base_overlay)
        bad["overrides"] = {
            "foundation/constraints/quality-scoring.yaml": {"dimensions": []}
        }
        bad["audit"] = dict(self.base_overlay["audit"])
        bad["audit"]["revision"] = 2
        from apps.drama.models import DramaConfigRevision

        DramaConfigRevision.objects.create(
            revision=2,
            overlay=bad,
            updated_by="admin",
            change_reason="bad seed",
        )
        with self.assertRaises(BusinessException) as ctx:
            self.svc.rollback(
                target_revision=2,
                change_reason="回滚到非法版本",
                actor="admin",
            )
        self.assertEqual(ctx.exception.code, CONFIG_OVERLAY_FORBIDDEN)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    LLM_ENABLED=False,
    CELERY_TASK_ALWAYS_EAGER=True,
)
class ProgressEventsLockTests(TransactionTestCase):
    def setUp(self):
        self.user = create_user()
        self.project = create_project(self.user)
        self.svc = GenerationService()
        self.job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.RUNNING,
            command_id="prog-lock",
            progress_events=[],
        )

    def test_concurrent_append_preserves_all_events(self):
        barrier = threading.Barrier(3)

        def append(i: int) -> None:
            barrier.wait()
            self.svc.append_progress(self.job, {"phase": f"step-{i}"})

        threads = [threading.Thread(target=append, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.job.refresh_from_db()
        phases = {e["phase"] for e in self.job.progress_events}
        self.assertEqual(phases, {"step-0", "step-1", "step-2"})


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    LLM_ENABLED=False,
    GENERATION_SSE_HEARTBEAT_SECONDS=0,
    GENERATION_SSE_MAX_WAIT_SECONDS=1,
)
class SSEEventTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.project = create_project(self.user)

    def test_sse_payload_helpers(self):
        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.COMPLETED,
            command_id="sse-1",
        )
        terminal = sse_terminal_event(job)
        self.assertTrue(terminal["done"])
        self.assertEqual(terminal["type"], "done")
        heartbeat = sse_heartbeat_event(job)
        self.assertEqual(heartbeat["type"], "heartbeat")
        self.assertFalse(heartbeat["done"])
        timeout = sse_timeout_event(job)
        self.assertEqual(timeout["type"], "timeout")
        self.assertTrue(timeout["done"])

    def test_sse_stream_emits_terminal_event(self):
        from apps.drama.views import _stream_generation_job

        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.COMPLETED,
            command_id="sse-stream",
            progress_events=[{"phase": "started"}],
        )
        response = _stream_generation_job(job)
        chunks = list(response.streaming_content)
        body = b"".join(chunks).decode("utf-8")
        self.assertIn('"type": "done"', body)
        self.assertIn('"done": true', body)

    def test_sse_stream_emits_timeout_when_max_wait_exceeded(self):
        from apps.drama.views import _stream_generation_job

        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.RUNNING,
            command_id="sse-timeout",
            progress_events=[],
        )
        response = _stream_generation_job(job)
        chunks = list(response.streaming_content)
        body = b"".join(chunks).decode("utf-8")
        self.assertIn('"type": "timeout"', body)

    def test_sse_accept_event_stream_not_406(self):
        """Accept: text/event-stream 必须通过 DRF 内容协商，不能 406。"""
        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.COMPLETED,
            command_id="sse-accept",
            progress_events=[{"phase": "started"}],
        )
        client = auth_client(self.user)
        response = client.get(
            f"/api/v1/drama/projects/{self.project.id}/generation/{job.id}/stream/",
            HTTP_ACCEPT="text/event-stream",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.get("Content-Type", "").startswith("text/event-stream")
        )
        body = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn('"type": "done"', body)
