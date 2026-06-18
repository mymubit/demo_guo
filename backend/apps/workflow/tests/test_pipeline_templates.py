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
        source = FusionPipelineDbService.ensure_builtin_default_pack()
        before = source.nodes.count()
        copy = FusionPipelineDbService.duplicate_pack(
            source.id,
            display_name="Copied Template",
            activate=False,
        )
        self.assertEqual(copy.nodes.count(), before)
        self.assertEqual(copy.display_name, "Copied Template")
        self.assertFalse(copy.is_active)

    def test_list_portal_pipelines_only_published(self):
        pack = FusionPipelineDbService.ensure_builtin_default_pack()
        FusionPipelineDbService.update_pack_meta(
            pack.id,
            {"is_published_to_portal": True, "display_name": "Five Step Main Chain"},
        )
        items = FusionPipelineDbService.list_portal_pipelines()
        self.assertTrue(any(row["id"] == str(pack.id) for row in items))

        FusionPipelineDbService.duplicate_pack(pack.id, display_name="Unpublished Copy", activate=False)
        unpublished = FusionPipelinePack.objects.filter(display_name="Unpublished Copy").first()
        self.assertIsNotNone(unpublished)
        items2 = FusionPipelineDbService.list_portal_pipelines()
        self.assertFalse(any(row["id"] == str(unpublished.id) for row in items2))
