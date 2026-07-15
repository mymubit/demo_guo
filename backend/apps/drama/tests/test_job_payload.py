# -*- coding: utf-8 -*-
"""GenerationJob 序列化测试。"""
from django.test import TestCase, override_settings

from apps.drama.job_payload import serialize_generation_job, sse_terminal_event
from apps.drama.models import DramaGenerationJob
from apps.drama.tests.helpers import create_project, create_user


@override_settings(DRAMA_SKILLS_ROOT="/workspace", LLM_ENABLED=False)
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
