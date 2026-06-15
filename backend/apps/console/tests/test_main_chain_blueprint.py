# -*- coding: utf-8 -*-
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

    def test_blueprint_returns_steps_and_catalog(self):
        resp = self.client.get("/api/admin/main-chain/blueprint/")
        self.assertEqual(resp.status_code, 200)
        data = resp.data["data"]
        self.assertIn("steps", data)
        self.assertIn("catalog", data)
        self.assertIn("post_script_chain", data)
        self.assertIn("meta", data)
        self.assertIn("execution_modes", data)
        self.assertIn("step", data["execution_modes"])
        self.assertIn("workspace", data["execution_modes"])

    def test_main_chain_steps_list(self):
        resp = self.client.get("/api/admin/main-chain/steps/")
        self.assertEqual(resp.status_code, 200)
        data = resp.data["data"]
        self.assertIn("items", data)
        self.assertIn("meta", data)

    def test_workflow_steps_deprecated(self):
        resp = self.client.get("/api/admin/workflow/steps/")
        self.assertEqual(resp.status_code, 404)

    def test_pipeline_steps_deprecated(self):
        resp = self.client.get("/api/admin/pipeline/steps/")
        self.assertEqual(resp.status_code, 404)

    def test_fusion_packs_deprecated(self):
        resp = self.client.get("/api/admin/fusion/packs/")
        self.assertEqual(resp.status_code, 404)

    def test_patch_registry_meta(self):
        resp = self.client.put(
            "/api/admin/main-chain/registry-meta/",
            {
                "post_script_chain": ["review", "score"],
                "post_script_append_agents": ["marketing"],
                "polish_max_rounds": 3,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["data"]["post_script_chain"], ["review", "score"])
        self.assertEqual(resp.data["data"]["polish_max_rounds"], 3)
