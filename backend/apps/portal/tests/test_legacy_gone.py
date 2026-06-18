# -*- coding: utf-8 -*-
"""Legacy API 下线 smoke 测试。"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.creation.models import Project

User = get_user_model()


class LegacyApiGoneTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            phone="13900009901",
            password="test-pass-123",
            is_staff=True,
            is_superuser=True,
        )
        self.user = User.objects.create_user(phone="13900009902", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            theme="test",
            core_idea="idea",
            episode_count=10,
            pipeline_mode=Project.MODE_WORKSPACE,
        )
        self.client.force_authenticate(user=self.user)

    def test_portal_confirm_returns_404(self):
        res = self.client.post(f"/api/creation/projects/{self.project.id}/confirm/", {}, format="json")
        self.assertEqual(res.status_code, 404)

    def test_works_run_agent_returns_410(self):
        res = self.client.post(
            f"/api/works/{self.project.id}/agents/brief/run/",
            {},
            format="json",
        )
        self.assertIn(res.status_code, (404, 410, 405))

    def test_admin_orchestration_flow_returns_404(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/admin/orchestration/flow/blueprint/")
        self.assertEqual(res.status_code, 404)

    def test_admin_agent_run_detail_ok_shape(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/admin/agent/runs/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("code"), 0)
