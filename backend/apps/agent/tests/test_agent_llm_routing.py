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
        self.assertEqual(NODE_PRESET_KEYS["node_script"], "glm-5")
        self.assertEqual(NODE_PRESET_KEYS["node_structure"], "ark-deepseek-v4-flash")

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
        from apps.workflow.pipeline_store import FusionPipelineDbService
        from apps.skill.llm.model_catalog import LlmCatalogService

        FusionPipelineDbService.ensure_builtin_default_pack()
        FusionPipelineDbService.clear_caches()
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

    def test_ensure_route_providers_binds_unbound_routes(self):
        from apps.agent.definition_service import AgentDefinitionService
        from apps.agent.models import AgentDefinition, AgentLlmRouteConfig
        from apps.skill.llm.providers import LlmProviderService
        from apps.skill.models import LlmProvider

        AgentDefinitionService.ensure_defaults()
        provider = LlmProvider.objects.filter(is_active=True, is_enabled=True).first()
        if provider is None:
            LlmProviderService.set_global_enabled(True)
            provider = LlmProvider.objects.create(
                name="测试 Provider",
                model_name="test-model",
                base_url="https://example.com/v1",
                is_enabled=True,
                is_active=True,
            )
        route = AgentLlmRouteConfig.objects.filter(route_key="adapt", is_active=True).first()
        self.assertIsNotNone(route)
        route.llm_provider = None
        route.save(update_fields=["llm_provider", "updated_at"])
        updated = AgentDefinitionService.ensure_route_providers()
        self.assertGreaterEqual(updated, 1)
        route.refresh_from_db()
        self.assertEqual(route.llm_provider_id, provider.id)
        agent = route.agent or AgentDefinition.objects.get(agent_id="adapt")
        self.assertTrue(AgentDefinitionService.health(agent)["route_ok"])

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
