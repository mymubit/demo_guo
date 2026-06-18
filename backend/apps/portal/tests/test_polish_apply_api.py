# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from apps.creation.artifact_service import save_artifact
from apps.creation.models import Project

User = get_user_model()


class PolishApplyApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900009001", password="test-pass-123")
        self.other = User.objects.create_user(phone="13900009002", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="polish-api",
            theme="overbearing-ceo",
            core_idea="润色 API 测试",
            episode_count=20,
            format_variant="B",
        )
        self.client = APIClient()
        self.url = f"/api/works/{self.project.id}/agents/polish/apply/"

    def test_apply_requires_auth(self):
        res = self.client.post(self.url, {"apply_all": True}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("code"), 401)

    def test_apply_empty_polish_log_returns_error(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post(self.url, {"apply_all": True}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("code"), 403)

    def test_apply_success_with_suggestions(self):
        save_artifact(
            self.project,
            "polish_log",
            {
                "suggestions": [
                    {
                        "index": 0,
                        "field": "dialogue",
                        "advice": "你好啊",
                        "episodeNumber": 1,
                    }
                ]
            },
        )
        save_artifact(
            self.project,
            "episode_scripts",
            {"episodes": [{"episodeNumber": 1, "title": "第1集", "dialogue": "你好"}]},
        )
        self.client.force_authenticate(user=self.user)
        res = self.client.post(self.url, {"indices": [0]}, format="json")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body.get("code"), 0)
        self.assertGreaterEqual(body.get("data", {}).get("appliedCount", 0), 1)

    def test_apply_forbidden_for_other_user(self):
        save_artifact(self.project, "polish_log", {"suggestions": []})
        self.client.force_authenticate(user=self.other)
        res = self.client.post(self.url, {"apply_all": True}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("code"), 403)
