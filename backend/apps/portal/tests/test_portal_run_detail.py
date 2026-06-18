# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.creation.models import AgentExecutionRun, Project
from apps.creation.monitoring.execution_run_service import AgentExecutionRunService

User = get_user_model()


class PortalRunDetailSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="13900008801", password="test-pass-123")
        self.staff = User.objects.create_user(
            phone="13900008802",
            password="test-pass-123",
            is_staff=True,
        )
        self.project = Project.objects.create(
            user=self.user,
            title="run-security",
            theme="sweet-pet",
            core_idea="测试 prompt 隐藏",
            episode_count=10,
            status=Project.STATUS_PENDING,
        )
        self.run = AgentExecutionRun.objects.create(
            project=self.project,
            user=self.user,
            agent_id="brief",
            status=AgentExecutionRun.STATUS_COMPLETED,
            rendered_prompt_preview="SECRET_SYSTEM_PROMPT\nSECRET_USER_PROMPT",
            input_snapshot={
                "required_artifacts": [],
                "artifacts": {"project_brief": {"coreHook": "敏感内容"}},
                "params": {"episode_from": 1},
            },
            input_artifact_keys=["project_brief"],
            estimated_prompt_tokens=1200,
        )

    def test_portal_run_detail_hides_prompt(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(
            f"/api/creation/projects/{self.project.id}/runs/{self.run.id}/",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json().get("data") or {}
        self.assertNotIn("rendered_prompt_preview", data)
        snapshot = data.get("input_snapshot") or {}
        self.assertNotIn("artifacts", snapshot)
        self.assertIn("input_artifact_keys", snapshot)
        self.assertEqual(snapshot.get("params"), {"episode_from": 1})

    def test_portal_runs_list_hides_prompt(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(
            f"/api/creation/projects/{self.project.id}/agents/brief/runs/",
        )
        self.assertEqual(res.status_code, 200)
        rows = res.json().get("data") or []
        self.assertGreaterEqual(len(rows), 1)
        self.assertNotIn("rendered_prompt_preview", rows[0])

    def test_admin_run_detail_includes_prompt(self):
        detail = AgentExecutionRunService.get_run_detail(str(self.run.id), include_sensitive=True)
        self.assertIn("rendered_prompt_preview", detail)
        self.assertIn("SECRET_SYSTEM_PROMPT", detail["rendered_prompt_preview"])
