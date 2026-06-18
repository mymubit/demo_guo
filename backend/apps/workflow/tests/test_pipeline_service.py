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
        FusionPipelineDbService.ensure_builtin_default_pack()
        self._seed_registry()
        FusionPipelineDbService.clear_caches()

        self.assertEqual(WorkflowPipelineService.creation_next_node_index(1), 2)
        self.assertEqual(WorkflowPipelineService.creation_next_node_index(2), 3)
        self.assertEqual(WorkflowPipelineService.creation_next_node_index(5), None)
