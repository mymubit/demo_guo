# -*- coding: utf-8 -*-
"""Main-chain Admin API 已下线。"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class MainChainBlueprintApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="13900007701",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_main_chain_endpoints_return_404(self):
        for path in (
            "/api/admin/main-chain/blueprint/",
            "/api/admin/main-chain/steps/",
            "/api/admin/main-chain/registry-meta/",
        ):
            resp = self.client.get(path) if path.endswith("/") and "registry-meta" not in path else None
            if path == "/api/admin/main-chain/registry-meta/":
                resp = self.client.put(path, {"polish_max_rounds": 3}, format="json")
            else:
                resp = self.client.get(path)
            self.assertEqual(resp.status_code, 404, path)

    def test_workflow_steps_deprecated(self):
        resp = self.client.get("/api/admin/workflow/steps/")
        self.assertEqual(resp.status_code, 404)

    def test_pipeline_steps_deprecated(self):
        resp = self.client.get("/api/admin/pipeline/steps/")
        self.assertEqual(resp.status_code, 404)

    def test_fusion_packs_deprecated(self):
        resp = self.client.get("/api/admin/fusion/packs/")
        self.assertEqual(resp.status_code, 404)
