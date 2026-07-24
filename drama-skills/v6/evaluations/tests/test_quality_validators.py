from __future__ import annotations

import unittest

from v6.engine.validators.quality import DIMENSIONS, apply_sa_veto, calculate_grade, delivery_decision, evolution_decision, revision_dimensions, validate_dimensions, validate_revision_scope


class QualityValidatorTests(unittest.TestCase):
    def test_ten_dimensions_are_exact_weighted_and_evidenced(self):
        items = [{"name": name, "weight": 0.1, "evidence": ["e"], "score": 80} for name in DIMENSIONS]
        self.assertEqual(validate_dimensions(items), [])
        items[0]["evidence"] = []
        self.assertTrue(validate_dimensions(items))

    def test_grade_and_revision_boundaries(self):
        self.assertEqual(calculate_grade(90), "S")
        self.assertEqual(calculate_grade(80), "A")
        self.assertEqual(calculate_grade(75), "B")
        self.assertEqual(revision_dimensions([{"name": "logic", "score": 40}]), ["logic"])

    def test_sa_veto_caps_grade_and_records_items(self):
        grade, vetoes = apply_sa_veto("S", 3.1, 2, False)
        self.assertEqual(grade, "B")
        self.assertEqual(len(vetoes), 3)
        self.assertEqual(apply_sa_veto("S", 3, 3, True), ("S", []))

    def test_revision_scope_protects_approved_artifacts(self):
        self.assertEqual(validate_revision_scope(["episode_scripts.episodes.8"]), [])
        self.assertTrue(validate_revision_scope(["story_bible.main_storyline"]))

    def test_evolution_uses_below_seventy_and_two_consecutive_batches(self):
        history = [{"overall_score": 69, "dimensions": {"logic": 69}}, {"overall_score": 68, "dimensions": {"logic": 68}}]
        result = evolution_decision(history)
        self.assertTrue(result["log_batch"])
        self.assertEqual(result["proposal_dimensions"], ["logic"])

    def test_delivery_gate_returns_gaps_and_blocks_marketing(self):
        preset = {"delivery_eligible": True, "pass_threshold": 75}
        quality = {"overall_score": 80}
        compliance = {"conclusion": "pass", "downstream_allowed": True}
        production = {"production_assessments": [{}], "budget_estimate": {"band": "medium"}, "release_check": {"policy_status": "verified-current", "release_ready": True}}
        self.assertTrue(delivery_decision(preset, quality, compliance, production)["deliverable"])
        quality["overall_score"] = 70
        blocked = delivery_decision(preset, quality, compliance, production)
        self.assertFalse(blocked["deliverable"])
        self.assertFalse(blocked["marketing_assets_allowed"])
