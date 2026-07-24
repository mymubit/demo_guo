from __future__ import annotations

import unittest

from v6.engine.validators.originality import PROTECTED_CLASSES, similarity_findings, validate_ai_assets, validate_comparison_conclusion, validate_protected_element_coverage, validate_rewrite_plan


class OriginalityValidatorTests(unittest.TestCase):
    def test_six_protected_classes_are_exact(self):
        self.assertEqual(validate_protected_element_coverage([{"class": item} for item in PROTECTED_CLASSES]), [])
        self.assertTrue(validate_protected_element_coverage([{"class": "character-name"}]))

    def test_similarity_thresholds_are_strictly_greater_than(self):
        self.assertEqual(similarity_findings(0.72, 0.80, 0.20), [])
        self.assertEqual(similarity_findings(0.721, 0.801, 0.201), ["title-semantic", "dialogue", "episode-position-structure"])

    def test_missing_comparison_cannot_claim_pass(self):
        self.assertEqual(validate_comparison_conclusion("not-completed", "not-completed"), [])
        self.assertTrue(validate_comparison_conclusion("not-completed", "pass"))

    def test_rewrite_changes_four_dimensions_and_not_only_names(self):
        dimensions = ["character-relationships", "scene", "timing", "causal-chain"]
        self.assertEqual(validate_rewrite_plan(dimensions, False), [])
        self.assertTrue(validate_rewrite_plan(dimensions[:-1], False))
        self.assertTrue(validate_rewrite_plan(dimensions, True))

    def test_ai_imitation_and_missing_label_are_rejected(self):
        valid = [{"id": "a1", "identifiable_imitation": False, "label_required": True, "label_status": "applied"}]
        self.assertEqual(validate_ai_assets(valid), [])
        valid[0]["identifiable_imitation"] = True
        self.assertTrue(validate_ai_assets(valid))
