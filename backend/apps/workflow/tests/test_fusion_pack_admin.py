# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.models import FusionPipelineNode, FusionPipelinePack


class FusionPipelinePackAdminApiTests(TestCase):
    def setUp(self):
        FusionPipelineDbService.clear_caches()
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser(
            phone="13900007701",
            password="test-pass-123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def tearDown(self):
        FusionPipelineDbService.clear_caches()

    def test_list_and_activate_pack(self):
        pack_a = FusionPipelinePack.objects.create(version="pack-a", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack_a,
            fusion_node_id="node-1-input",
            chain_order=1,
            website_index=1,
            name="立项",
        )
        pack_b = FusionPipelinePack.objects.create(version="pack-b", is_active=False)
        FusionPipelineNode.objects.create(
            pack=pack_b,
            fusion_node_id="node-1-input",
            chain_order=1,
            website_index=1,
            name="立项 B",
        )
        FusionPipelineDbService.clear_caches()

        list_res = self.client.get("/api/admin/main-chain/fusion/packs/")
        self.assertEqual(list_res.status_code, 200)
        items = list_res.data["data"]["items"]
        versions = {item["version"] for item in items}
        self.assertIn("pack-a", versions)
        self.assertIn("pack-b", versions)

        activate_res = self.client.post(f"/api/admin/main-chain/fusion/packs/{pack_b.id}/activate/")
        self.assertEqual(activate_res.status_code, 200)
        pack_a.refresh_from_db()
        pack_b.refresh_from_db()
        self.assertFalse(pack_a.is_active)
        self.assertTrue(pack_b.is_active)

        steps = FusionPipelineDbService.get_active_pack().nodes.first()
        self.assertEqual(steps.name, "立项 B")
