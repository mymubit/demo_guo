# -*- coding: utf-8 -*-
"""GenerationJob 序列化测试。"""
from django.test import TestCase, override_settings

from apps.drama.job_payload import serialize_generation_job, sse_terminal_event
from apps.drama.models import DramaGenerationJob
from apps.drama.tests.helpers import SKILLS_ROOT, create_project, create_user


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class JobPayloadTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.project = create_project(self.user)

    def test_serialize_generation_job_shape(self):
        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.QUEUED,
            request_payload={"role": "drama.topic-director"},
            progress_events=[{"phase": "started", "message": "任务开始"}],
        )
        data = serialize_generation_job(job)
        self.assertEqual(data["job_id"], str(job.id))
        self.assertEqual(data["project_id"], str(self.project.id))
        self.assertEqual(data["status"], "queued")
        self.assertEqual(data["role"], "drama.topic-director")
        self.assertIn("created_at", data)

    def test_external_review_title_prefers_script_title(self):
        job = DramaGenerationJob.objects.create(
            owner=self.user,
            project=None,
            job_type=DramaGenerationJob.JobType.EXTERNAL_REVIEW,
            status=DramaGenerationJob.Status.FAILED,
            request_payload={
                "source_filename": "宫斗逆袭.txt",
                "script_title": "宫斗逆袭",
                "script_content": "# 正文标题\n第一场",
            },
        )
        data = serialize_generation_job(job)
        self.assertEqual(data["title"], "宫斗逆袭")
        self.assertEqual(data["source_filename"], "宫斗逆袭.txt")

    def test_external_review_title_falls_back_to_filename(self):
        job = DramaGenerationJob.objects.create(
            owner=self.user,
            project=None,
            job_type=DramaGenerationJob.JobType.EXTERNAL_REVIEW,
            status=DramaGenerationJob.Status.QUEUED,
            request_payload={
                "source_filename": "投稿A.md",
                "script_content": "第一场 内景",
            },
        )
        data = serialize_generation_job(job)
        self.assertEqual(data["title"], "投稿A.md")
        self.assertEqual(data["source_filename"], "投稿A.md")

    def test_external_review_title_falls_back_to_first_line(self):
        job = DramaGenerationJob.objects.create(
            owner=self.user,
            project=None,
            job_type=DramaGenerationJob.JobType.EXTERNAL_REVIEW,
            status=DramaGenerationJob.Status.COMPLETED,
            request_payload={"script_content": "# 玉碎宫门\n第一集"},
        )
        data = serialize_generation_job(job)
        self.assertEqual(data["title"], "玉碎宫门")
        self.assertIsNone(data["source_filename"])

    def test_sse_terminal_event_for_disabled(self):
        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.DISABLED,
            request_payload={},
            error_message="LLM 已禁用",
        )
        event = sse_terminal_event(job)
        self.assertEqual(event["type"], "done")
        self.assertEqual(event["status"], "disabled")
        self.assertTrue(event["done"])

    def test_failed_job_progress_is_zero(self):
        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.FAILED,
            progress_events=[
                {"phase": "started"},
                {"phase": "llm_started"},
                {"phase": "llm_done"},
            ],
            error_message="Schema 校验失败",
        )
        data = serialize_generation_job(job)
        self.assertEqual(data["progress"], 0)
        self.assertEqual(data["status"], "failed")

    def test_running_llm_wait_progress_creeps_with_time(self):
        from apps.drama.job_payload import compute_progress_from_events, sse_heartbeat_event

        events = [
            {"phase": "started", "message": "任务开始", "ts": "2026-01-01T00:00:00+00:00"},
            {
                "phase": "llm_started",
                "ts": "2020-01-01T00:00:00+00:00",  # 很久以前 → 等待进度应上浮
            },
        ]
        progress = compute_progress_from_events(
            events, status=DramaGenerationJob.Status.RUNNING
        )
        self.assertGreaterEqual(progress, 40)
        self.assertLessEqual(progress, 55)

        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.RUNNING,
            progress_events=events,
        )
        heartbeat = sse_heartbeat_event(job)
        self.assertEqual(heartbeat["type"], "heartbeat")
        self.assertIsInstance(heartbeat["progress"], int)
        self.assertGreaterEqual(heartbeat["progress"], 40)

    def test_sse_progress_event_includes_numeric_progress(self):
        from apps.drama.job_payload import sse_event_from_progress

        job = DramaGenerationJob.objects.create(
            project=self.project,
            job_type=DramaGenerationJob.JobType.GENERATION,
            status=DramaGenerationJob.Status.RUNNING,
            progress_events=[],
        )
        events = [
            {"phase": "started", "message": "任务开始"},
            {"phase": "llm_started"},
        ]
        payload = sse_event_from_progress(
            job, events[1], events_prefix=events
        )
        self.assertEqual(payload["type"], "progress")
        self.assertIsInstance(payload["progress"], int)
        self.assertGreaterEqual(payload["progress"], 18)
        self.assertEqual(payload["message"], "正在调用模型…")
