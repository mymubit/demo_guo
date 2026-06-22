# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.creation.artifact_service import save_artifact
from apps.creation.models import Project

User = get_user_model()


class CreationWorkspaceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(phone="13900004406", password="test-pass-123")
        self.other = User.objects.create_user(phone="13900004407", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="api-workspace",
            theme="sweet-pet",
            core_idea="api test",
            episode_count=10,
            pipeline_mode=Project.MODE_WORKSPACE,
        )
        save_artifact(
            self.project,
            "project_brief",
            {
                "workingTitle": "api-workspace",
                "theme": "sweet-pet",
                "episodeCount": 10,
                "coreHook": "api test",
            },
        )
        self.client.force_authenticate(user=self.user)

    def test_get_workspace_payload(self):
        from apps.agent.definition_service import AgentDefinitionService

        AgentDefinitionService.ensure_defaults()
        res = self.client.get(f"/api/creation/projects/{self.project.id}/workspace/")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("code"), 0)
        data = body.get("data") or {}
        project = data.get("project") or {}
        self.assertIn("can_download", project)
        self.assertIn("can_share", project)
        self.assertFalse(project["can_share"])
        agents = data.get("agents") or []
        self.assertGreaterEqual(len(agents), 5)
        self.assertIn("agent_id", agents[0])
        self.assertIn("health", agents[0])
        artifact_keys = {row.get("artifact_key") for row in (data.get("artifacts") or [])}
        self.assertIn("project_brief", artifact_keys)

    def test_legacy_agent_content_returns_404(self):
        put_res = self.client.put(
            f"/api/creation/projects/{self.project.id}/agents/1/content/",
            {"fields": [{"key": "themeDisplayName", "value": "sweet-pet-api"}]},
            format="json",
        )
        self.assertEqual(put_res.status_code, 404)

    def test_share_pending_project_forbidden(self):
        res = self.client.post(f"/api/creation/share/{self.project.id}/", {}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("code"), 403)

    def test_share_completed_project_ok(self):
        save_artifact(
            self.project,
            "episode_scripts",
            {"episodes": [{"episodeNumber": 1, "title": "ep1", "full_script_text": "body"}]},
        )
        res = self.client.post(f"/api/creation/share/{self.project.id}/", {}, format="json")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("code"), 0)
        self.assertTrue((body.get("data") or {}).get("share_token"))

    def test_workspace_can_share_field_via_api(self):
        res = self.client.get(f"/api/creation/projects/{self.project.id}/workspace/")
        project = (res.json().get("data") or {}).get("project") or {}
        self.assertFalse(project.get("can_share"))
        save_artifact(
            self.project,
            "episode_scripts",
            {"episodes": [{"episodeNumber": 1, "title": "ep1", "full_script_text": "body"}]},
        )
        res = self.client.get(f"/api/creation/projects/{self.project.id}/workspace/")
        project = (res.json().get("data") or {}).get("project") or {}
        self.assertTrue(project.get("can_share"))
