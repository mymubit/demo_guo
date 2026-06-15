# -*- coding: utf-8 -*-
from django.test import SimpleTestCase, TestCase, override_settings

from apps.agent.routes import AgentLlmRouteService
from apps.skill.llm.setup_provisioning import (
    AGENT_PRESET_KEYS,
    NODE_PRESET_KEYS,
    AgentLlmRoutingService,
)


class AgentLlmRoutingUnitTests(SimpleTestCase):
    def test_node_preset_coverage(self):
        self.assertEqual(NODE_PRESET_KEYS["node-5-script"], "glm-5")
        self.assertEqual(NODE_PRESET_KEYS["node-2-structure"], "ark-deepseek-v4-flash")

    def test_glm5_is_native(self):
        self.assertTrue(AgentLlmRoutingService.is_native_preset("glm-5"))
        self.assertFalse(AgentLlmRoutingService.is_native_preset("ark-deepseek-v4-flash"))

    def test_agent_preset_coverage(self):
        self.assertEqual(AGENT_PRESET_KEYS["polish"], "doubao-seed-2.0-lite")


class AgentLlmRoutingDbTests(TestCase):
    @override_settings(
        VOLCANO_ARK_API_KEY="test-volcano-key",
        VOLCANO_EP_DEEPSEEK_V4_FLASH="ep-ds-flash",
        VOLCANO_EP_DOUBAO_LITE="ep-lite",
        ZHIPU_API_KEY="test-zhipu-key",
        ZHIPU_GLM5_MODEL="glm-5",
    )
    def test_provision_and_bind(self):
        from apps.workflow.step_admin import PipelineStepAdminService
        from apps.skill.llm.model_catalog import LlmCatalogService

        LlmCatalogService.ensure_seed_catalog()
        provider_map = AgentLlmRoutingService.provision_all_providers()
        self.assertIn("ark-deepseek-v4-flash", provider_map)
        self.assertIn("doubao-seed-2.0-lite", provider_map)
        self.assertIn("glm-5", provider_map)

        bound_nodes = AgentLlmRoutingService.bind_fusion_node_providers(provider_map)
        self.assertEqual(bound_nodes, len(NODE_PRESET_KEYS))

        bound_agents = AgentLlmRoutingService.bind_agent_route_providers(provider_map)
        self.assertEqual(bound_agents, len(AGENT_PRESET_KEYS))

        script_pid = AgentLlmRouteService.resolve_provider_id("script")
        self.assertEqual(script_pid, provider_map["glm-5"])

        polish_pid = AgentLlmRouteService.resolve_provider_id("polish")
        self.assertEqual(polish_pid, provider_map["doubao-seed-2.0-lite"])

    @override_settings(
        VOLCANO_ARK_API_KEY="test-volcano-key",
        ZHIPU_API_KEY="test-zhipu-key",
    )
    def test_provision_with_model_id_without_ep_env(self):
        from apps.skill.llm.model_catalog import LlmCatalogService

        LlmCatalogService.ensure_seed_catalog()
        provider_map = AgentLlmRoutingService.provision_volcano_providers()
        self.assertIn("ark-deepseek-v4-flash", provider_map)
        self.assertIn("doubao-seed-2.0-lite", provider_map)
