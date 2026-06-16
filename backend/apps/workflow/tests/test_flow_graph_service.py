# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.models import AgentRegistryConfig
from apps.agent.runtime import get_agent_registry
from apps.creation.models import CreationNode, Project
from apps.workflow.models import FusionPipelineNode, FusionPipelinePack
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.services.flow_graph_service import FlowGraphPlanService


class FlowGraphPlanServiceTests(TestCase):
    def tearDown(self):
        FusionPipelineDbService.clear_caches()
        get_agent_registry.cache_clear()

    def _seed_chain(self):
        pack = FusionPipelinePack.objects.create(version="flow-graph-test", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-a",
            chain_order=1,
            website_index=1,
            name="A",
            portal_visible=True,
            enabled=True,
        )
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-b",
            chain_order=2,
            website_index=3,
            name="B",
            portal_visible=True,
            enabled=True,
        )
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-c",
            chain_order=3,
            website_index=2,
            name="C",
            portal_visible=True,
            enabled=True,
        )
        config, _ = AgentRegistryConfig.objects.update_or_create(
            config_key="default",
            defaults={"is_active": True},
        )
        config.is_active = True
        config.registry = {
            "agents": [{"id": "brief", "workspace_index": 1}],
            "_meta": {
                "flow_graph": {
                    "parallel_groups": [
                        {
                            "id": "g1",
                            "label": "并行组1",
                            "node_ids": ["node-b", "node-c"],
                        }
                    ],
                    "edges": [],
                }
            },
        }
        config.save()
        get_agent_registry.cache_clear()
        FusionPipelineDbService.clear_caches()

    def test_build_execution_stages_with_parallel_group(self):
        self._seed_chain()
        stages = FlowGraphPlanService.build_execution_stages()
        self.assertEqual(len(stages), 2)
        self.assertEqual(stages[0]["type"], "single")
        self.assertEqual(stages[0]["indices"], [1])
        self.assertEqual(stages[1]["type"], "parallel")
        self.assertEqual(stages[1]["indices"], [3, 2])

    def test_creation_next_node_index_skips_parallel_block(self):
        self._seed_chain()
        self.assertEqual(FlowGraphPlanService.creation_next_node_index(1), 3)
        self.assertIsNone(FlowGraphPlanService.creation_next_node_index(2))

    def test_pending_parallel_indices(self):
        self._seed_chain()
        user = get_user_model().objects.create_user(phone="13900008801", password="pass-123")
        project = Project.objects.create(user=user, title="p", episode_count=10)
        CreationNode.objects.create(
            project=project,
            node_index=3,
            node_name="B",
            status=CreationNode.STATUS_COMPLETED,
        )
        pending = FlowGraphPlanService.pending_parallel_indices(project, 3)
        self.assertEqual(pending, [2])

    def test_branch_edge_review_passed_routes_to_target(self):
        pack = FusionPipelinePack.objects.create(version="flow-graph-branch", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-a",
            chain_order=1,
            website_index=1,
            name="A",
            portal_visible=True,
            enabled=True,
        )
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-b",
            chain_order=2,
            website_index=2,
            name="B",
            portal_visible=True,
            enabled=True,
        )
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-c",
            chain_order=3,
            website_index=3,
            name="C",
            portal_visible=True,
            enabled=True,
        )
        config, _ = AgentRegistryConfig.objects.update_or_create(
            config_key="default",
            defaults={"is_active": True},
        )
        config.is_active = True
        config.registry = {
            "agents": [{"id": "brief", "workspace_index": 1}],
            "_meta": {
                "flow_graph": {
                    "parallel_groups": [],
                    "edges": [
                        {
                            "from": "node-a",
                            "to": "node-c",
                            "type": "branch",
                            "condition": {"kind": "review_passed"},
                        },
                        {
                            "from": "node-a",
                            "to": "node-b",
                            "type": "default",
                        },
                    ],
                }
            },
        }
        config.save()
        get_agent_registry.cache_clear()
        FusionPipelineDbService.clear_caches()

        user = get_user_model().objects.create_user(phone="13900008802", password="pass-123")
        project = Project.objects.create(user=user, title="branch", episode_count=10)
        CreationNode.objects.create(
            project=project,
            node_index=6,
            node_name="Review",
            status=CreationNode.STATUS_COMPLETED,
        )

        self.assertEqual(FlowGraphPlanService.next_node_index_for_project(project, 1), 3)
        CreationNode.objects.filter(project=project, node_index=6).update(status=CreationNode.STATUS_FAILED)
        self.assertEqual(FlowGraphPlanService.next_node_index_for_project(project, 1), 2)

    def test_enrich_portal_chain_adds_orchestration_hints(self):
        self._seed_chain()
        chain = FlowGraphPlanService.enrich_portal_chain(
            [{"index": 1, "fusion_node_id": "node-a", "name": "A"}]
        )
        self.assertEqual(chain[0].get("orchestration_stage_type"), "single")

        parallel_chain = FlowGraphPlanService.enrich_portal_chain(
            [
                {"index": 3, "fusion_node_id": "node-b", "name": "B"},
                {"index": 2, "fusion_node_id": "node-c", "name": "C"},
            ]
        )
        self.assertEqual(parallel_chain[0].get("orchestration_stage_type"), "parallel")
        self.assertEqual(parallel_chain[0].get("orchestration_parallel_peers"), [2])
