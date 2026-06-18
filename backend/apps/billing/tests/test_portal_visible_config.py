# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.workflow.services.pipeline_service import WorkflowPipelineService
from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.models import FusionPipelineNode, FusionPipelinePack
from apps.workflow.step_admin import PipelineStepAdminService


class PortalVisibleConfigTests(TestCase):
    def tearDown(self):
        FusionPipelineDbService.clear_caches()

    def test_portal_main_chain_excludes_hidden_nodes_from_db(self):
        pack = FusionPipelinePack.objects.create(version="test-portal-visible", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-1-input",
            chain_order=1,
            website_index=1,
            name="创意立项",
            enabled=True,
            portal_visible=True,
            coin_cost=5,
        )
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-6-review",
            chain_order=6,
            website_index=6,
            name="质检审查",
            enabled=True,
            portal_visible=False,
            coin_cost=10,
        )
        FusionPipelineDbService.clear_caches()

        hidden = WorkflowPipelineService.portal_hidden_fusion_node_ids(pack_id=str(pack.id))
        self.assertIn("node-6-review", hidden)

        chain_ids = {n["fusion_node_id"] for n in WorkflowPipelineService.portal_main_chain(pack_id=str(pack.id))}
        self.assertIn("node-1-input", chain_ids)
        self.assertNotIn("node-6-review", chain_ids)

    def test_list_steps_reads_unified_node_fields(self):
        pack = FusionPipelinePack.objects.create(version="test-board", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-6-review",
            chain_order=6,
            website_index=6,
            name="质检审查",
            enabled=True,
            portal_visible=False,
            coin_cost=10,
        )
        FusionPipelineDbService.clear_caches()

        review = next(
            (n for n in PipelineStepAdminService.list_steps() if n.get("fusion_node_id") == "node-6-review"),
            None,
        )
        self.assertIsNotNone(review)
        self.assertFalse(review.get("portal_visible"))
