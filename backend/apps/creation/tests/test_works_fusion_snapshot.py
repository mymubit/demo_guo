# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.creation.artifact_service import save_artifact
from apps.creation.models import Project
from apps.creation.services.works import get_project_detail

User = get_user_model()


class WorksFusionSnapshotTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900008910", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="快照测试",
            theme="sweet-pet",
            episode_count=10,
            status=Project.STATUS_COMPLETED,
            fusion_status=Project.FUSION_READY,
            overall_score=88,
            grade="A",
        )
        save_artifact(
            self.project,
            "script_score_report",
            {"overallScore": 88, "grade": "A"},
        )
        save_artifact(
            self.project,
            "review_report",
            {"passed": True, "issues": ["节奏略快"]},
        )
        save_artifact(
            self.project,
            "marketing_kit",
            {"titles": ["标题1"], "clipHooks": ["钩子1"]},
        )

    def test_get_project_detail_includes_fusion_snapshot(self):
        detail = get_project_detail(str(self.project.id), self.user)
        snapshot = detail.get("fusion_snapshot")
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["overall_score"], 88)
        self.assertEqual(snapshot["score_report"]["overallScore"], 88)
        self.assertTrue(snapshot["review_report"]["passed"])
        self.assertEqual(snapshot["marketing_kit"]["titles"], ["标题1"])
        self.assertIn("result_html", detail)
        self.assertNotIn("rendered_result_html", detail)

    def test_works_detail_api_returns_fusion_snapshot(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        resp = client.get(f"/api/works/{self.project.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        snapshot = resp.data["data"].get("fusion_snapshot")
        self.assertIsNotNone(snapshot)
        self.assertIn("score_report", snapshot)
