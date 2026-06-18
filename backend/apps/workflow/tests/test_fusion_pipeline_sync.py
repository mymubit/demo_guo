# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.workflow.models import FusionPipelineNode, FusionPipelinePack
from apps.workflow.pipeline_store import FusionPipelineDbService


class FusionPipelineDbOnlyTests(TestCase):
    def tearDown(self):
        FusionPipelineDbService.clear_caches()

    def test_builtin_default_pack_is_five_step_db_only(self):
        pack = FusionPipelineDbService.ensure_builtin_default_pack()
        node_ids = list(pack.nodes.order_by("chain_order").values_list("fusion_node_id", flat=True))
        self.assertEqual(
            node_ids,
            ["node_brief", "node_structure", "node_character", "node_outline", "node_script"],
        )
        self.assertEqual(pack.terminal_node_ids, ["node_script"])
        self.assertEqual(pack.post_script_chain, [])

    def test_removed_disk_entrypoints_are_not_runtime_paths(self):
        self.assertFalse(hasattr(FusionPipelineDbService, "sync_from_disk"))
        self.assertFalse(hasattr(FusionPipelineDbService, "import_from_disk"))

    def test_duplicate_pack_normalizes_agent_runner_path(self):
        pack = FusionPipelinePack.objects.create(version="duplicate-runner-test", is_active=True)
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id="node_structure",
            chain_order=1,
            website_index=2,
            name="Structure",
            runner_type="fusion_node",
            runner_path="apps.creation.agents.world.run_world_agent",
        )
        FusionPipelineDbService.clear_caches()

        copied = FusionPipelineDbService.duplicate_pack(pack.id, display_name="Copied Pack")

        node = FusionPipelineNode.objects.get(pack=copied, fusion_node_id="node_structure")
        self.assertEqual(node.runner_path, "apps.creation.step_mode.run_orchestrator_step")
