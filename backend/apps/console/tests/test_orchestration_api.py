# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class OrchestrationAdminApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="13900007702",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_orchestration_stats(self):
        resp = self.client.get("/api/admin/orchestration/stats/?limit=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.data["data"]
        self.assertIn("skills", data)

    def test_agent_catalog_canonical(self):
        resp = self.client.get("/api/admin/agent/catalog/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("workspaceAgents", resp.data["data"])

    def test_legacy_agents_prefix_deprecated(self):
        for path in (
            "/api/admin/agents/catalog/",
            "/api/admin/agents/stats/",
            "/api/admin/agents/projects/00000000-0000-0000-0000-000000000001/traces/",
            "/api/admin/agents/execution-runs/00000000-0000-0000-0000-000000000001/",
        ):
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 404, path)
