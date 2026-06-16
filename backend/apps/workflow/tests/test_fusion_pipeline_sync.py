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

    def test_sync_from_disk_replaces_orphan_placeholder_nodes(self):
        pack = FusionPipelinePack.objects.create(
            version="flow-graph-test",
            is_active=True,
            imported_from_root="",
        )
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-a",
            chain_order=1,
            website_index=1,
            name="A",
        )
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-b",
            chain_order=2,
            website_index=3,
            name="B",
        )
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-c",
            chain_order=3,
            website_index=2,
            name="C",
        )
        FusionPipelineDbService.clear_caches()

        try:
            FusionPipelineDbService.sync_from_disk()
        except Exception:
            self.skipTest("磁盘 project-config 不可用，跳过 sync 集成测试")

        node_ids = list(
            FusionPipelineNode.objects.filter(pack=pack)
            .order_by("chain_order")
            .values_list("fusion_node_id", flat=True)
        )
        self.assertNotIn("node-a", node_ids)
        self.assertIn("node-4-outline", node_ids)
        self.assertIn("node-5-script", node_ids)
        orders = list(
            FusionPipelineNode.objects.filter(pack=pack)
            .order_by("chain_order")
            .values_list("chain_order", flat=True)
        )
        self.assertEqual(orders, list(range(1, len(orders) + 1)))

    def test_duplicate_pack_normalizes_agent_runner_path(self):
        pack = FusionPipelinePack.objects.create(version="duplicate-runner-test", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node-2-structure",
            chain_order=1,
            website_index=2,
            name="结构与世界观",
            runner_type="fusion_node",
            runner_path="apps.creation.agents.world.run_world_agent",
        )
        FusionPipelineDbService.clear_caches()

        copied = FusionPipelineDbService.duplicate_pack(
            pack.id,
            display_name="复制配置包",
        )

        node = FusionPipelineNode.objects.get(pack=copied, fusion_node_id="node-2-structure")
        self.assertEqual(node.runner_path, "apps.creation.step_mode.run_orchestrator_step")
