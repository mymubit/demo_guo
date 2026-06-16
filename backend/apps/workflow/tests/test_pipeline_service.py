# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.agent.models import AgentRegistryConfig
from apps.agent.runtime import get_agent_registry
from apps.workflow.models import FusionPipelineNode, FusionPipelinePack
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.services.pipeline_service import WorkflowPipelineService
from apps.workflow.step_admin import PipelineStepAdminService


class WorkflowPipelineServiceTests(TestCase):
    def tearDown(self):
        FusionPipelineDbService.clear_caches()
        get_agent_registry.cache_clear()

    def _seed_registry(self):
        AgentRegistryConfig.objects.update_or_create(
            config_key="default",
            defaults={
                "is_active": True,
                "registry": {"agents": [], "_meta": {}},
            },
        )
        get_agent_registry.cache_clear()

    def test_creation_next_node_index_follows_chain_order(self):
        pack = FusionPipelinePack.objects.create(version="chain-order-next", is_active=True)
        node_a = FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-a",
            chain_order=1,
            website_index=1,
            name="A",
            portal_visible=True,
            enabled=True,
        )
        node_b = FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-b",
            chain_order=2,
            website_index=3,
            name="B",
            portal_visible=True,
            enabled=True,
        )
        node_c = FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-c",
            chain_order=3,
            website_index=2,
            name="C",
            portal_visible=True,
            enabled=True,
        )
        self._seed_registry()
        FusionPipelineDbService.clear_caches()

        self.assertEqual(WorkflowPipelineService.creation_next_node_index(1), 3)
        self.assertEqual(WorkflowPipelineService.creation_next_node_index(3), 2)
        self.assertIsNone(WorkflowPipelineService.creation_next_node_index(2))

        PipelineStepAdminService.reorder_steps([str(node_c.id), str(node_a.id), str(node_b.id)])
        FusionPipelineDbService.clear_caches()

        self.assertEqual(WorkflowPipelineService.creation_next_node_index(2), 1)
        self.assertEqual(WorkflowPipelineService.creation_next_node_index(1), 3)
        self.assertIsNone(WorkflowPipelineService.creation_next_node_index(3))
