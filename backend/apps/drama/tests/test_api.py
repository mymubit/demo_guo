# -*- coding: utf-8 -*-
"""API 权限与契约集成测试。"""
from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.tests.helpers import FIXTURE_SETTINGS, auth_client, create_project, create_user


@override_settings(
    DRAMA_SKILLS_ROOT="/workspace",
    LLM_ENABLED=False,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class DramaApiTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.other = create_user(username="other")
        self.staff = User.objects.create_user(
            username="admin",
            password="test-pass-123",
            is_staff=True,
        )
        self.project = create_project(self.user)
        self.client = auth_client(self.user)

    def test_list_projects_requires_auth(self):
        resp = self.client.get("/api/v1/drama/projects/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)

    def test_settings_put_requires_if_match(self):
        resp = self.client.put(
            f"/api/v1/drama/projects/{self.project.id}/settings/",
            FIXTURE_SETTINGS,
            format="json",
        )
        self.assertEqual(resp.data["code"], 4001)

    def test_settings_put_with_etag(self):
        payload = dict(FIXTURE_SETTINGS)
        payload["project_id"] = str(self.project.id)
        resp = self.client.put(
            f"/api/v1/drama/projects/{self.project.id}/settings/",
            payload,
            format="json",
            HTTP_IF_MATCH="1",
        )
        self.assertEqual(resp.data["code"], 0)
        self.assertEqual(resp["ETag"], "2")

    def test_other_user_cannot_read_project(self):
        client = auth_client(self.other)
        resp = client.get(f"/api/v1/drama/projects/{self.project.id}/workflow/")
        self.assertEqual(resp.data["code"], 403)

    def test_admin_config_forbidden_for_regular_user(self):
        resp = self.client.get("/api/v1/drama/admin/config/")
        self.assertEqual(resp.data["code"], 403)

    def test_admin_config_readable_by_staff(self):
        client = auth_client(self.staff)
        resp = client.get("/api/v1/drama/admin/config/")
        self.assertEqual(resp.data["code"], 0)

    def test_generation_disabled_without_llm(self):
        resp = self.client.post(
            f"/api/v1/drama/projects/{self.project.id}/generation/start/",
            {
                "command_id": "api-gen-disabled",
                "expected_version": 0,
                "role": "drama.topic-director",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 202)
        job_id = resp.data["data"]["job_id"]
        status_resp = self.client.get(
            f"/api/v1/drama/projects/{self.project.id}/generation/{job_id}/"
        )
        self.assertEqual(status_resp.data["data"]["status"], "disabled")

    def test_workflow_command_api(self):
        resp = self.client.post(
            f"/api/v1/drama/projects/{self.project.id}/workflow/commands/",
            {
                "command_id": "api-cmd-1",
                "event": "project_brief_completed",
                "expected_version": 0,
            },
            format="json",
        )
        self.assertEqual(resp.data["code"], 0)
        self.assertEqual(resp.data["data"]["current_phase"], "blueprint")

    def test_theme_matrix_endpoint(self):
        resp = self.client.get("/api/v1/drama/theme-matrix/")
        self.assertEqual(resp.data["code"], 0)
        self.assertIn("dim_order", resp.data["data"])
        self.assertIn("axes", resp.data["data"])

    def test_generation_start_returns_unified_job(self):
        resp = self.client.post(
            f"/api/v1/drama/projects/{self.project.id}/generation/start/",
            {
                "command_id": "api-gen-1",
                "expected_version": 0,
                "role": "drama.topic-director",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 202)
        data = resp.data["data"]
        self.assertIn("job_id", data)
        self.assertIn("status", data)
        self.assertIn("project_id", data)
        self.assertIn("project_id", data)
        self.assertIn("role", data)
        self.assertIn("command_id", data)
        self.assertEqual(data["project_id"], str(self.project.id))

    def test_external_review_job_access_without_project(self):
        resp = self.client.post(
            "/api/v1/drama/external-script-reviews/",
            {
                "command_id": "ext-1",
                "scoring_preset": "standard",
                "check_mode": "standard",
                "script_content": "测试剧本",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 202)
        job_id = resp.data["data"]["job_id"]
        status_resp = self.client.get(f"/api/v1/drama/jobs/{job_id}/")
        self.assertEqual(status_resp.data["code"], 0)
        self.assertEqual(status_resp.data["data"]["job_id"], job_id)

    def test_other_user_cannot_read_orphan_job(self):
        resp = self.client.post(
            "/api/v1/drama/external-script-reviews/",
            {
                "command_id": "ext-2",
                "scoring_preset": "standard",
                "check_mode": "standard",
                "script_content": "私密剧本",
            },
            format="json",
        )
        job_id = resp.data["data"]["job_id"]
        other = auth_client(self.other)
        denied = other.get(f"/api/v1/drama/jobs/{job_id}/")
        self.assertEqual(denied.data["code"], 403)

    def test_project_summary_includes_entry_type(self):
        resp = self.client.get("/api/v1/drama/projects/")
        self.assertEqual(resp.data["code"], 0)
        item = resp.data["data"][0]
        self.assertEqual(item["entry_type"], "original_track")
