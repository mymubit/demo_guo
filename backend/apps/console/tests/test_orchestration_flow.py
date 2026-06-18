# -*- coding: utf-8 -*-
"""Orchestration flow Admin API 已下线。"""
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
        FusionPipelineNode.objects.create(
            pack=self.pack,
            fusion_node_id="node-a",
            chain_order=1,
            website_index=1,
            name="A",
        )
        FusionPipelineNode.objects.create(
            pack=self.pack,
            fusion_node_id="node-b",
            chain_order=2,
            website_index=2,
            name="B",
        )

    def test_orchestration_flow_endpoints_return_404(self):
        for method, path, body in (
            ("get", "/api/admin/orchestration/flow/blueprint/", None),
            (
                "put",
                "/api/admin/orchestration/flow/steps/reorder/",
                {"ordered_ids": []},
            ),
            (
                "put",
                "/api/admin/orchestration/flow/registry-meta/",
                {"flow_graph": {"edges": [], "parallel_groups": []}},
            ),
            ("post", "/api/admin/orchestration/flow/publish/", {}),
            ("get", "/api/admin/orchestration/recent-runs/?limit=10", None),
        ):
            if method == "get":
                resp = self.client.get(path)
            elif method == "put":
                resp = self.client.put(path, body, format="json")
            else:
                resp = self.client.post(path, body, format="json")
            self.assertEqual(resp.status_code, 404, path)
