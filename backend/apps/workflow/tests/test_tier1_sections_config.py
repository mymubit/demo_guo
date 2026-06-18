# -*- coding: utf-8 -*-
from django.test import SimpleTestCase, TestCase

from apps.agent.binding import (
    agent_id_for_fusion_node,
    resolve_tier1_sections_for_agent,
    resolve_tier1_sections_for_node,
)
from apps.agent.registry import AgentRegistryConfigService
from apps.agent.models import AgentRegistryConfig
from apps.workflow.models import FusionPipelineNode, FusionPipelinePack
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.step_admin import PipelineStepAdminService
from apps.agent.bootstrap.tier1_sections import AGENT_TIER1_SEED, NODE_TIER1_SEED
from apps.workflow.tier1_sections import resolve_tier1_sections


class AgentNodeBindingTests(TestCase):
    def tearDown(self):
        FusionPipelineDbService.clear_caches()
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()

    def _seed_pipeline_and_registry(self):
        pack = FusionPipelinePack.objects.create(version="bind-test", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node_structure",
            chain_order=2,
            website_index=2,
            name="缁撴瀯",
        )
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node_script",
            chain_order=5,
            website_index=5,
            name="鍓ф湰",
        )
        AgentRegistryConfig.objects.update_or_create(
            config_key="default",
            defaults={
                "is_active": True,
                "registry": {
                    "agents": [
                        {"id": "world", "workspace_index": 2},
                        {"id": "script", "workspace_index": 5},
                    ],
                    "_meta": {
                        "workspace_modules": [
                        {"index": 2, "agent_id": "structure"},
                            {"index": 5, "agent_id": "script"},
                        ]
                    },
                },
            },
        )
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()
        FusionPipelineDbService.clear_caches()

    def test_agent_id_for_fusion_node_via_registry(self):
        self._seed_pipeline_and_registry()
        self.assertEqual(agent_id_for_fusion_node("node_structure"), "structure")
        self.assertEqual(agent_id_for_fusion_node("node_script"), "script")

    def test_resolve_tier1_sections_for_agent_uses_seed(self):
        sections = resolve_tier1_sections_for_agent("structure")
        self.assertEqual(sections, AGENT_TIER1_SEED["structure"])


class Tier1SectionsConfigTests(TestCase):
    def tearDown(self):
        FusionPipelineDbService.clear_caches()
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()

    def _seed_registry(self, agents):
        AgentRegistryConfig.objects.update_or_create(
            config_key="default",
            defaults={
                "is_active": True,
                "registry": {"agents": agents, "_meta": {}},
            },
        )
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()

    def test_resolve_tier1_sections_reads_agent_registry(self):
        pack = FusionPipelinePack.objects.create(version="test-tier1-db", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node_script",
            chain_order=1,
            website_index=5,
            name="鍓ф湰鍒涗綔",
        )
        self._seed_registry(
            [
                {
                    "id": "script",
                    "workspace_index": 5,
                    "tier1_sections": ["custom_section_a", "custom_section_b"],
                }
            ]
        )
        FusionPipelineDbService.clear_caches()

        sections = resolve_tier1_sections("node_script")
        self.assertEqual(sections, ["custom_section_a", "custom_section_b"])

    def test_resolve_tier1_sections_falls_back_to_agent_defaults(self):
        pack = FusionPipelinePack.objects.create(version="test-tier1-empty", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node_script",
            chain_order=1,
            website_index=5,
            name="璐ㄩ噺瀹℃煡",
        )
        self._seed_registry([{"id": "script", "workspace_index": 5}])
        FusionPipelineDbService.clear_caches()
        self.assertEqual(resolve_tier1_sections("node_script"), AGENT_TIER1_SEED["script"])

    def test_main_chain_nodes_exposes_agent_id(self):
        pack = FusionPipelinePack.objects.create(version="test-tier1-chain", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node_outline",
            chain_order=1,
            website_index=4,
            name="澶х翰",
        )
        self._seed_registry([{"id": "outline", "workspace_index": 4}])
        FusionPipelineDbService.clear_caches()

        nodes = FusionPipelineDbService.main_chain_nodes(pack_id=str(pack.id))
        outline = next(n for n in nodes if n["fusion_node_id"] == "node_outline")
        self.assertEqual(outline.get("agent_id"), "outline")
        self.assertNotIn("skill_id", outline)
        self.assertNotIn("tier1_sections", outline)


class PipelineStepTier1Tests(TestCase):
    def tearDown(self):
        FusionPipelineDbService.clear_caches()
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()

    def _seed_registry(self, agents):
        AgentRegistryConfig.objects.update_or_create(
            config_key="default",
            defaults={
                "is_active": True,
                "registry": {"agents": agents, "_meta": {}},
            },
        )
        from apps.agent.runtime import get_agent_registry

        get_agent_registry.cache_clear()

    def test_list_steps_reads_active_pack(self):
        pack = FusionPipelinePack.objects.create(version="test-discover-nodes", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node_brief",
            chain_order=1,
            website_index=1,
            name="Brief",
        )
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node_structure",
            chain_order=2,
            website_index=2,
            name="缁撴瀯瑙勫垝",
        )
        self._seed_registry(
            [
                {"id": "brief", "workspace_index": 1},
                {"id": "structure", "workspace_index": 2},
            ]
        )
        FusionPipelineDbService.clear_caches()

        steps = PipelineStepAdminService.list_steps()
        node_ids = [n["node_id"] for n in steps]
        self.assertEqual(node_ids, ["node_brief", "node_structure"])
        self.assertEqual(steps[0]["display_name"], "Brief")
        self.assertEqual(steps[0]["agent_id"], "brief")
        self.assertNotIn("skill_id", steps[0])

    def test_update_tier1_sections_writes_agent_registry(self):
        pack = FusionPipelinePack.objects.create(version="test-tier1-prompt", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node_script",
            chain_order=1,
            website_index=5,
            name="鍓ф湰鍒涗綔",
        )
        self._seed_registry([{"id": "script", "workspace_index": 5}])
        FusionPipelineDbService.clear_caches()

        ok = PipelineStepAdminService.update_tier1_sections(
            "node_script",
            ["writing_prohibitions", "dialogue_quality"],
        )
        self.assertTrue(ok)
        self.assertEqual(
            resolve_tier1_sections("node_script"),
            ["writing_prohibitions", "dialogue_quality"],
        )


class Tier1SectionsFallbackTests(SimpleTestCase):
    def test_resolve_tier1_sections_unknown_node_returns_empty(self):
        self.assertEqual(resolve_tier1_sections_for_node("node-unknown"), [])

    def test_tier1_section_catalog_matches_renderers(self):
        from apps.skill.skills.loader import _TIER1_RENDERERS

        catalog = PipelineStepAdminService.tier1_section_catalog()
        self.assertEqual(catalog, sorted(_TIER1_RENDERERS.keys()))

    def test_tier1_section_catalog_detail_has_labels(self):
        detail = PipelineStepAdminService.tier1_section_catalog_detail()
        self.assertTrue(detail)
        self.assertTrue(all(item.get("key") and item.get("label") for item in detail))


class DefaultUserTemplateConfigTests(SimpleTestCase):
    def test_get_default_user_template_returns_module_constant(self):
        from apps.workflow.prompt_seed import DEFAULT_USER_TEMPLATE, get_default_user_template

        self.assertEqual(get_default_user_template(), DEFAULT_USER_TEMPLATE)

