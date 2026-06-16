# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.agent.runtime import get_agent_registry
from apps.agent.registry import AgentRegistryConfigService
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.agent.models import AgentRegistryConfig
from apps.workflow.models import FusionPipelineNode, FusionPipelinePack
from apps.workflow.step_admin import PipelineStepAdminService
from apps.workflow.tier1_sections import resolve_tier1_sections


class PipelineStepAdminServiceTests(TestCase):
    def tearDown(self):
        FusionPipelineDbService.clear_caches()
        get_agent_registry.cache_clear()

    def _seed_script_agent(self):
        AgentRegistryConfig.objects.update_or_create(
            config_key="default",
            defaults={
                "is_active": True,
                "registry": {
                    "agents": [{"id": "script", "workspace_index": 5}],
                    "_meta": {},
                },
            },
        )
        get_agent_registry.cache_clear()

    def test_update_step_persists_orchestration_and_agent_skill(self):
        pack = FusionPipelinePack.objects.create(version="test-unified-step", is_active=True)
        node = FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-5-script",
            chain_order=5,
            website_index=5,
            name="剧本创作",
            coin_cost=30,
            portal_visible=True,
        )
        self._seed_script_agent()
        FusionPipelineDbService.clear_caches()

        updated = PipelineStepAdminService.update_step(
            str(node.id),
            {
                "display_name": "剧本生成",
                "coin_cost": 25,
                "portal_visible": False,
                "system_prompt": "custom system",
                "tier1_sections": ["scoring", "dialogue_quality"],
            },
        )
        self.assertIsNotNone(updated)
        node.refresh_from_db()
        self.assertEqual(node.name, "剧本生成")
        self.assertEqual(node.coin_cost, 25)
        self.assertFalse(node.portal_visible)
        self.assertEqual(resolve_tier1_sections("node-5-script"), ["scoring", "dialogue_quality"])

        row = AgentRegistryConfigService.get_active_row()
        script = next(a for a in (row.registry or {}).get("agents", []) if a.get("id") == "script")
        self.assertEqual((script.get("prompt") or {}).get("system"), "custom system")

    def test_list_steps_returns_active_pack_nodes(self):
        pack = FusionPipelinePack.objects.create(version="test-list-steps", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-1-input",
            chain_order=1,
            website_index=1,
            name="立项",
        )
        AgentRegistryConfig.objects.update_or_create(
            config_key="default",
            defaults={
                "is_active": True,
                "registry": {"agents": [{"id": "brief", "workspace_index": 1}], "_meta": {}},
            },
        )
        get_agent_registry.cache_clear()
        FusionPipelineDbService.clear_caches()

        steps = PipelineStepAdminService.list_steps()
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["node_id"], "node-1-input")
        self.assertEqual(steps[0]["agent_id"], "brief")
        self.assertNotIn("skill_id", steps[0])

    def test_reorder_steps_updates_chain_order(self):
        pack = FusionPipelinePack.objects.create(version="test-reorder", is_active=True)
        node_a = FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-a",
            chain_order=1,
            website_index=1,
            name="A",
        )
        node_b = FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-b",
            chain_order=2,
            website_index=2,
            name="B",
        )
        FusionPipelineDbService.clear_caches()

        steps = PipelineStepAdminService.reorder_steps([str(node_b.id), str(node_a.id)])
        self.assertEqual([s["node_id"] for s in steps], ["node-b", "node-a"])
        node_a.refresh_from_db()
        node_b.refresh_from_db()
        self.assertEqual(node_b.chain_order, 1)
        self.assertEqual(node_a.chain_order, 2)
