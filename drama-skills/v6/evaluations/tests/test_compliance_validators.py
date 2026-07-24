from __future__ import annotations

import unittest

from v6.engine.validators.compliance import DIMENSIONS, classify_horror, decide_compliance, validate_delivery_materials, validate_dimensions, validate_harmful_behavior_framing, validate_justice_closure, validate_platform_declaration, validate_whitewash_markers


class ComplianceValidatorTests(unittest.TestCase):
    def test_horror_levels_map_to_canonical_severity(self):
        self.assertEqual(classify_horror("extreme"), "P0")
        self.assertEqual(classify_horror("high-risk"), "P1")
        self.assertEqual(classify_horror("medium-risk"), "P2")

    def test_nine_dimensions_are_exact_and_unique(self):
        valid = [{"name": name, "status": "pass"} for name in DIMENSIONS]
        self.assertEqual(validate_dimensions(valid), [])
        self.assertTrue(validate_dimensions(valid[:-1]))

    def test_platform_requires_verified_version(self):
        self.assertEqual(validate_platform_declaration("p", "2026-07", "verified"), [])
        self.assertTrue(validate_platform_declaration("p", None, "not-checked"))
        self.assertEqual(validate_platform_declaration(None, None, "not-checked"), [])

    def test_p0_and_open_p1_stop_downstream(self):
        p0 = decide_compliance([{"severity": "P0", "status": "open"}], [])
        p1 = decide_compliance([{"severity": "P1", "status": "open"}], [])
        self.assertEqual(p0, {"conclusion": "block", "downstream_allowed": False})
        self.assertEqual(p1, {"conclusion": "revise", "downstream_allowed": False})

    def test_p2_does_not_block_when_checks_complete(self):
        result = decide_compliance([{"severity": "P2", "status": "open"}], [{"status": "pass"}])
        self.assertEqual(result, {"conclusion": "pass", "downstream_allowed": True})

    def test_unchecked_dimension_cannot_pass(self):
        result = decide_compliance([], [{"status": "not-checked"}])
        self.assertEqual(result["conclusion"], "revise")

    def test_delivery_pass_requires_all_materials(self):
        self.assertEqual(validate_delivery_materials({"script": True}, "pass"), [])
        self.assertTrue(validate_delivery_materials({"script": True, "quality": False}, "pass"))

    def test_justice_thresholds_preserve_v5_counts(self):
        crimes = [{"id": index} for index in range(5)]
        closures = [{"story_progress": 0.2}, {"story_progress": 0.5}, {"story_progress": 0.7}]
        self.assertEqual(validate_justice_closure(crimes, closures), [])
        self.assertTrue(validate_justice_closure(crimes, closures[:2]))

    def test_crime_below_trigger_does_not_require_closure(self):
        self.assertEqual(validate_justice_closure([{"id": 1}], []), [])

    def test_justice_closure_must_reach_final_thirty_five_percent(self):
        crimes = [{"id": 1}, {"id": 2}]
        self.assertTrue(validate_justice_closure(crimes, [{"story_progress": 0.2}, {"story_progress": 0.6}]))

    def test_sympathy_marker_keeps_responsibility_and_consequence(self):
        valid = [{"id": "m1", "responsibility_retained": True, "consequence_present": True}]
        self.assertEqual(validate_whitewash_markers(valid), [])
        valid[0]["consequence_present"] = False
        self.assertTrue(validate_whitewash_markers(valid))

    def test_harmful_behavior_may_not_be_glorified_without_accountability(self):
        valid = [{"id": "h1", "glorified": False, "responsibility_retained": False, "consequence_present": False}]
        self.assertEqual(validate_harmful_behavior_framing(valid), [])
        valid[0]["glorified"] = True
        self.assertTrue(validate_harmful_behavior_framing(valid))
