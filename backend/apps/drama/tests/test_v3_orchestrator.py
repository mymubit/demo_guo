# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.drama.models import V3CommandRun, V3Project
from apps.drama.orchestrator import dispatch_command


class V3OrchestratorTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="orch", password="pass12345")

    def test_create_project_succeeds_sync(self) -> None:
        run = dispatch_command(
            owner=self.user,
            command_type="create_project",
            payload={"title": "新剧", "entry_type": "adapt"},
        )
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        self.assertIsNotNone(run.project_id)
        project = V3Project.objects.get(id=run.project_id)
        self.assertEqual(project.title, "新剧")
        self.assertEqual(project.entry_type, "adapt")
        self.assertEqual(project.stage, "topic")
        self.assertEqual(str(run.result_payload.get("project_id")), str(project.id))

    def test_unknown_async_stub_empty(self) -> None:
        """W5 起 ASYNC_STUB 已清空；未知命令仍 failed。"""
        run = dispatch_command(
            owner=self.user,
            command_type="not_a_real_command",
            payload={},
        )
        self.assertEqual(run.status, V3CommandRun.Status.FAILED)
        self.assertIn("未知", run.error_message)

    def test_unknown_command_fails(self) -> None:
        run = dispatch_command(
            owner=self.user,
            command_type="create-project-brief",
            payload={},
        )
        self.assertEqual(run.status, V3CommandRun.Status.FAILED)
