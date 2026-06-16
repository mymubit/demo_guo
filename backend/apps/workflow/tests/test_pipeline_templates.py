# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.workflow.models import FusionPipelinePack
from apps.workflow.pipeline_store import FusionPipelineDbService


class FusionPipelineTemplateTests(TestCase):
    def setUp(self):
        FusionPipelineDbService.clear_caches()

    def tearDown(self):
        FusionPipelineDbService.clear_caches()

    def test_duplicate_pack_copies_nodes(self):
        FusionPipelineDbService.import_from_disk(activate=True)
        source = FusionPipelineDbService.get_active_pack()
        self.assertIsNotNone(source)
        before = source.nodes.count()
        copy = FusionPipelineDbService.duplicate_pack(
            source.id,
            display_name="测试副本",
            activate=False,
        )
        self.assertEqual(copy.nodes.count(), before)
        self.assertEqual(copy.display_name, "测试副本")
        self.assertFalse(copy.is_active)

    def test_list_portal_pipelines_only_published(self):
        FusionPipelineDbService.import_from_disk(activate=True)
        pack = FusionPipelineDbService.get_active_pack()
        FusionPipelineDbService.update_pack_meta(
            pack.id,
            {"is_published_to_portal": True, "display_name": "标准主链"},
        )
        items = FusionPipelineDbService.list_portal_pipelines()
        self.assertTrue(any(row["id"] == str(pack.id) for row in items))

        FusionPipelineDbService.duplicate_pack(pack.id, display_name="未发布副本", activate=False)
        unpublished = FusionPipelinePack.objects.filter(display_name="未发布副本").first()
        self.assertIsNotNone(unpublished)
        items2 = FusionPipelineDbService.list_portal_pipelines()
        self.assertFalse(any(row["id"] == str(unpublished.id) for row in items2))
