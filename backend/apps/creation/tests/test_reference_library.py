# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.creation.reference_library import (
    enrich_reversal_point,
    lookup_hook_type,
    lookup_reversal_pattern,
    suggest_hooks_for_intensity,
    summarize_hook_types,
    summarize_reversal_patterns,
)
from apps.skill.config.portal.reference_libs import ReferenceLibraryService


class ReferenceLibraryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from django.core.management import call_command

        call_command(
            "absorb_external_assets",
            source=["demo4book", "ai-drama-skills-v2"],
            write=True,
            overwrite=True,
            verbosity=0,
        )
        ReferenceLibraryService.clear_cache()

    def test_summarize_libraries_non_empty(self):
        hooks = summarize_hook_types(limit=5)
        patterns = summarize_reversal_patterns(limit=5)
        self.assertGreater(len(hooks), 0)
        self.assertGreater(len(patterns), 0)
        self.assertIn("code", hooks[0])
        self.assertIn("name", patterns[0])

    def test_lookup_hook_type_known_code(self):
        hooks = summarize_hook_types(limit=1)
        if not hooks:
            self.skipTest("no hooks in library")
        row = lookup_hook_type(hooks[0]["code"])
        self.assertIsNotNone(row)
        self.assertEqual(row["code"], hooks[0]["code"])

    def test_enrich_reversal_point_adds_technique_and_pattern(self):
        out = enrich_reversal_point(
            {
                "episodeNumber": 12,
                "reversalType": "identity-reveal",
                "description": "女主真实身份曝光",
            }
        )
        self.assertEqual(out["techniqueCode"], "RV-01")
        self.assertEqual(out["techniqueLabel"], "隐藏身份大揭秘")
        self.assertTrue(out.get("patternName") or out.get("patternCode"))

    def test_lookup_reversal_pattern_known_code(self):
        patterns = summarize_reversal_patterns(limit=1)
        if not patterns:
            self.skipTest("no reversal patterns in library")
        row = lookup_reversal_pattern(patterns[0]["code"])
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], patterns[0]["name"])

    def test_suggest_hooks_for_intensity_returns_codes(self):
        hooks = suggest_hooks_for_intensity(9, limit=3)
        self.assertGreater(len(hooks), 0)
        self.assertIn("code", hooks[0])
        self.assertIn("name", hooks[0])

    def test_backfill_reversal_codes_adds_pattern_code(self):
        from apps.creation.reference_library import backfill_reversal_codes

        out = backfill_reversal_codes(
            [{"episodeNumber": 5, "reversalType": "identity-reveal", "description": "身份曝光"}]
        )
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].get("reversalCode"))

    def test_enrich_rhythm_block_view_links_reversals(self):
        from apps.creation.reference_library import enrich_rhythm_block_view

        block = enrich_rhythm_block_view(
            {
                "episodeRange": "1-10",
                "episodeStart": 1,
                "episodeEnd": 10,
                "intensityLevel": 8,
            },
            reversals=[
                {
                    "episodeNumber": 5,
                    "reversalTypeLabel": "身份揭晓",
                    "patternName": "隐藏身份大揭秘",
                    "patternCode": "REV-ID-01",
                }
            ],
        )
        self.assertGreater(len(block.get("suggestedHooks") or []), 0)
        self.assertEqual(len(block.get("linkedReversals") or []), 1)
