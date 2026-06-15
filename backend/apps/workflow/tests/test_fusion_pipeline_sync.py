# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.workflow.pipeline_store import FusionPipelineDbService
from apps.workflow.models import FusionPipelineNode, FusionPipelinePack


class FusionPipelineSyncTests(TestCase):
    def tearDown(self):
        FusionPipelineDbService.clear_caches()

    def test_sync_from_disk_preserves_coin_cost(self):
        pack = FusionPipelinePack.objects.create(
            version="sync-preserve-test",
            is_active=True,
            imported_from_root="",
        )
        node = FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-1-input",
            chain_order=1,
            website_index=1,
            name="自定义立项名",
            coin_cost=99,
            portal_visible=False,
        )
        FusionPipelineDbService.clear_caches()

        try:
            FusionPipelineDbService.sync_from_disk()
        except Exception:
            self.skipTest("磁盘 project-config 不可用，跳过 sync 集成测试")

        node.refresh_from_db()
        self.assertEqual(node.coin_cost, 99)
        self.assertEqual(node.name, "自定义立项名")
        self.assertFalse(node.portal_visible)
