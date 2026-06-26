# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.agent.definition_service import AgentDefinitionService
from apps.agent.registry import AgentRegistryConfigService


class AgentRegistryConfigServiceTests(TestCase):
    def test_validate_registry_rejects_empty_agents(self):
        ok, message = AgentRegistryConfigService.validate_registry({"agents": []})
        self.assertFalse(ok)
        self.assertIn("agents", message)

    def test_admin_payload_reads_drama_definitions(self):
        AgentDefinitionService.ensure_defaults()
        AgentRegistryConfigService.clear_cache()
        payload = AgentRegistryConfigService.admin_payload()
        self.assertEqual(payload["source"], "drama_definitions")
        self.assertTrue(payload["registry"].get("agents"))
        self.assertIn("drama.topic-director", payload["default_tier1_sections_by_agent"])

    def test_save_registry_is_disabled(self):
        with self.assertRaises(ValueError):
            AgentRegistryConfigService.save_registry({"agents": [{"id": "drama.topic-director"}]})


class AgentRegistryAdminApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="13900007701",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        AgentDefinitionService.ensure_defaults()

    def test_get_agent_registry_returns_readonly_payload(self):
        resp = self.client.get("/api/admin/agent/registry/")
        self.assertEqual(resp.status_code, 200)
        data = resp.data["data"]
        self.assertEqual(data["source"], "drama_definitions")
        self.assertTrue(data["registry"].get("agents"))
        self.assertTrue(data.get("_deprecated"))

    def test_put_agent_registry_returns_410(self):
        resp = self.client.put(
            "/api/admin/agent/registry/",
            {"registry": {"agents": [{"id": "drama.topic-director"}]}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.data.get("code"), 0)
