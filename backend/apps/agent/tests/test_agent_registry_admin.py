# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.agent.registry import AgentRegistryConfigService
from apps.agent.models import AgentRegistryConfig


class AgentRegistryConfigServiceTests(TestCase):
    def test_validate_registry_rejects_empty_agents(self):
        ok, message = AgentRegistryConfigService.validate_registry({"agents": []})
        self.assertFalse(ok)
        self.assertIn("agents", message)

    def test_save_registry_persists_active_row(self):
        registry = {
            "_meta": {"version": "test", "post_script_chain": ["review", "score"]},
            "agents": [{"id": "brief", "name": "Brief", "runner": "apps.creation.orchestration.brief.run_brief_agent"}],
        }
        row = AgentRegistryConfigService.save_registry(registry)
        self.assertTrue(row.is_active)
        payload = AgentRegistryConfigService.admin_payload()
        self.assertEqual(payload["source"], "db")
        self.assertEqual(payload["registry"]["_meta"]["post_script_chain"], ["review", "score"])

    def test_save_registry_normalizes_legacy_runner_path(self):
        registry = {
            "agents": [
                {
                    "id": "world",
                    "name": "World",
                    "runner": "apps.creation.agents.world.run_world_agent",
                }
            ]
        }
        row = AgentRegistryConfigService.save_registry(registry)
        self.assertEqual(
            row.registry["agents"][0]["runner"],
            "apps.creation.orchestration.world.run_world_agent",
        )

    def test_patch_agent_normalizes_legacy_runner_path(self):
        AgentRegistryConfigService.save_registry(
            {"agents": [{"id": "world", "name": "World"}]},
        )
        AgentRegistryConfigService.patch_agent(
            "world",
            {"runner": "apps.creation.agents.world.run_world_agent"},
        )
        row = AgentRegistryConfigService.get_active_row()
        self.assertEqual(
            row.registry["agents"][0]["runner"],
            "apps.creation.orchestration.world.run_world_agent",
        )

    def test_ensure_defaults_imports_from_disk(self):
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()
        AgentRegistryConfigService.ensure_defaults()
        row = AgentRegistryConfigService.get_active_row()
        self.assertIsNotNone(row)
        self.assertTrue(row.registry.get("agents"))
        get_agent_registry.cache_clear()
        registry = get_agent_registry()
        self.assertEqual(registry.get("_registry_source"), "db")


class AgentRegistryAdminApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="13900007701",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_get_agent_registry_returns_payload(self):
        AgentRegistryConfig.objects.update_or_create(
            config_key="default",
            defaults={
                "registry": {
                    "_meta": {"version": "9.9.9"},
                    "agents": [{"id": "brief", "name": "Brief"}],
                },
                "is_active": True,
            },
        )
        resp = self.client.get("/api/admin/agent/registry/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["data"]["source"], "db")
        self.assertEqual(resp.data["data"]["registry"]["_meta"]["version"], "9.9.9")
        self.assertIsInstance(resp.data["data"].get("tier1_section_catalog"), list)
        self.assertIsInstance(resp.data["data"].get("tier1_section_catalog_detail"), list)
        self.assertIn("brief", resp.data["data"].get("default_tier1_sections_by_agent", {}))

    def test_put_agent_registry_saves(self):
        body = {
            "registry": {
                "_meta": {"post_script_append_agents": ["marketing"]},
                "agents": [
                    {
                        "id": "marketing",
                        "name": "Marketing",
                        "runner": "apps.creation.orchestration.marketing.run_marketing_agent",
                    }
                ],
            }
        }
        resp = self.client.put("/api/admin/agent/registry/", body, format="json")
        self.assertEqual(resp.status_code, 200)
        row = AgentRegistryConfig.objects.filter(config_key="default", is_active=True).first()
        self.assertIsNotNone(row)
        self.assertEqual(row.registry["agents"][0]["id"], "marketing")
