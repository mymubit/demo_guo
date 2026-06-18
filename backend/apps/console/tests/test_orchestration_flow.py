# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.workflow.models import FusionPipelineNode, FusionPipelinePack


class OrchestrationFlowApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            phone="13900007702",
            password="admin-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.pack = FusionPipelinePack.objects.create(version="orch-flow-test", is_active=True)
        self.node_a = FusionPipelineNode.objects.create(
            pack=self.pack,
            fusion_node_id="node-a",
            chain_order=1,
            website_index=1,
            name="A",
        )
        self.node_b = FusionPipelineNode.objects.create(
            pack=self.pack,
            fusion_node_id="node-b",
            chain_order=2,
            website_index=2,
            name="B",
        )

    def test_flow_blueprint_alias(self):
        resp = self.client.get("/api/admin/orchestration/flow/blueprint/")
        self.assertEqual(resp.status_code, 200)
        data = resp.data["data"]
        self.assertIn("steps", data)
        self.assertIn("flow_graph", data)

    def test_flow_steps_reorder(self):
        resp = self.client.put(
            "/api/admin/orchestration/flow/steps/reorder/",
            {"ordered_ids": [str(self.node_b.id), str(self.node_a.id)]},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        steps = resp.data["data"]["steps"]
        self.assertEqual([s["node_id"] for s in steps], ["node-b", "node-a"])

    def test_flow_registry_meta_flow_graph(self):
        resp = self.client.put(
            "/api/admin/orchestration/flow/registry-meta/",
            {
                "flow_graph": {
                    "edges": [{"from": "node-a", "to": "node-b", "type": "sequential"}],
                    "parallel_groups": [],
                },
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("post_script_chain", resp.data["data"])
        self.assertEqual(resp.data["data"]["explicit_post_agents"], ["review", "score", "polish", "marketing", "insight"])
        self.assertIn("edges", resp.data["data"]["flow_graph"])

    def test_flow_publish_and_publish_state(self):
        self.client.put(
            "/api/admin/orchestration/flow/registry-meta/",
            {
                "flow_graph": {
                    "edges": [{"from": "node-a", "to": "node-b", "type": "sequential"}],
                    "parallel_groups": [],
                },
            },
            format="json",
        )
        bp = self.client.get("/api/admin/orchestration/flow/blueprint/")
        self.assertEqual(bp.status_code, 200)
        publish_state = bp.data["data"].get("publish_state") or {}
        self.assertIn("current_checksum", publish_state)

        resp = self.client.post("/api/admin/orchestration/flow/publish/", {}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("version", resp.data["data"])

        bp2 = self.client.get("/api/admin/orchestration/flow/blueprint/")
        state2 = bp2.data["data"].get("publish_state") or {}
        self.assertFalse(state2.get("is_dirty"))

    def test_recent_runs_endpoint(self):
        resp = self.client.get("/api/admin/orchestration/recent-runs/?limit=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.data["data"]
        self.assertIn("runs", data)
        self.assertIn("node_states", data)
