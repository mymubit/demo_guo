# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.models import AgentRegistryConfig
from apps.agent.runtime import get_agent_registry
from apps.creation.models import AgentExecutionRun, Project
from apps.workflow.models import FusionPipelineNode, FusionPipelinePack
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.services.flow_graph_service import FlowGraphPlanService


class FlowGraphPlanServiceTests(TestCase):
    def tearDown(self):
        FusionPipelineDbService.clear_caches()
        get_agent_registry.cache_clear()

    def _seed_chain(self, *, edges=None):
        flow_graph = {
            "parallel_groups": [
                {
                    "id": "g1",
                    "label": "parallel",
                    "node_ids": ["node_structure", "node_character"],
                }
            ],
            "edges": edges or [],
        }
        pack = FusionPipelinePack.objects.create(
            version="flow-graph-test",
            is_active=True,
            terminal_node_ids=["node_script"],
            flow_graph=flow_graph,
        )
        specs = [
            ("node_brief", 1, 1, "Brief"),
            ("node_structure", 2, 2, "Structure"),
            ("node_character", 3, 3, "Character"),
            ("node_outline", 4, 4, "Outline"),
            ("node_script", 5, 5, "Script"),
        ]
        for node_id, order, index, name in specs:
            FusionPipelineNode.objects.create(
                pack=pack,
                fusion_node_id=node_id,
                chain_order=order,
                website_index=index,
                name=name,
                portal_visible=True,
                enabled=True,
            )
        config, _ = AgentRegistryConfig.objects.update_or_create(
            config_key="default",
            defaults={"is_active": True},
        )
        config.is_active = True
        config.registry = {
            "agents": [
                {"id": "brief", "workspace_index": 1},
                {"id": "structure", "workspace_index": 2},
                {"id": "character", "workspace_index": 3},
                {"id": "outline", "workspace_index": 4},
                {"id": "script", "workspace_index": 5},
            ],
            "_meta": {},
        }
        config.save()
        get_agent_registry.cache_clear()
        FusionPipelineDbService.clear_caches()

    def test_build_execution_stages_with_parallel_group(self):
        self._seed_chain()
        stages = FlowGraphPlanService.build_execution_stages()
        self.assertEqual([s["type"] for s in stages[:3]], ["single", "parallel", "single"])
        self.assertEqual(stages[0]["indices"], [1])
        self.assertEqual(stages[1]["indices"], [2, 3])

    def test_creation_next_node_index_skips_parallel_block(self):
        self._seed_chain()
        self.assertEqual(FlowGraphPlanService.creation_next_node_index(1), 2)
        self.assertEqual(FlowGraphPlanService.creation_next_node_index(3), 4)

    def test_pending_parallel_indices(self):
        self._seed_chain()
        user = get_user_model().objects.create_user(phone="13900008801", password="pass-123")
        project = Project.objects.create(user=user, title="p", episode_count=10)
        AgentExecutionRun.objects.create(
            project=project,
            user=user,
            agent_id="structure",
            node_index=2,
            status=AgentExecutionRun.STATUS_COMPLETED,
        )
        pending = FlowGraphPlanService.pending_parallel_indices(project, 2)
        self.assertEqual(pending, [3])

    def test_branch_edge_defaults_do_not_use_removed_review_node(self):
        self._seed_chain(
            edges=[
                {"from": "node_brief", "to": "node_character", "type": "branch", "condition": {"kind": "always"}},
                {"from": "node_brief", "to": "node_structure", "type": "default"},
            ]
        )
        user = get_user_model().objects.create_user(phone="13900008802", password="pass-123")
        project = Project.objects.create(user=user, title="branch", episode_count=10)
        self.assertEqual(FlowGraphPlanService.next_node_index_for_project(project, 1), 3)

    def test_enrich_portal_chain_adds_orchestration_hints(self):
        self._seed_chain()
        chain = FlowGraphPlanService.enrich_portal_chain(
            [{"index": 1, "fusion_node_id": "node_brief", "name": "Brief"}]
        )
        self.assertEqual(chain[0].get("orchestration_stage_type"), "single")

        parallel_chain = FlowGraphPlanService.enrich_portal_chain(
            [
                {"index": 2, "fusion_node_id": "node_structure", "name": "Structure"},
                {"index": 3, "fusion_node_id": "node_character", "name": "Character"},
            ]
        )
        self.assertEqual(parallel_chain[0].get("orchestration_stage_type"), "parallel")
        self.assertEqual(parallel_chain[0].get("orchestration_parallel_peers"), [3])
