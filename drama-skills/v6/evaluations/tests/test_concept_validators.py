from __future__ import annotations

import unittest

from v6.engine.validators.concept import validate_concept_risk_boundary, validate_elevator_pitch, validate_market_fields, validate_one_core_action


class ConceptValidatorTests(unittest.TestCase):
    def test_exactly_one_core_action(self):
        self.assertEqual(validate_one_core_action(["expose"]), [])
        self.assertTrue(validate_one_core_action([]))
        self.assertTrue(validate_one_core_action(["expose", "escape"]))

    def test_elevator_pitch_requires_all_elements(self):
        pitch = {key: "value" for key in ["protagonist_identity", "urgent_goal", "core_obstacle", "differentiating_mechanism", "without_proper_nouns"]}
        self.assertEqual(validate_elevator_pitch(pitch), [])
        del pitch["core_obstacle"]
        self.assertTrue(validate_elevator_pitch(pitch))

    def test_project_brief_requires_integrated_market_judgment(self):
        fields = ["synopsis", "audience_channel", "market_opportunity", "blockbuster_factors", "competitor_references", "differentiation_strategy", "first_episode_hook", "first_paywall_direction", "subject_sensitivity_precheck"]
        self.assertEqual(validate_market_fields({key: "value" for key in fields}), [])
        self.assertTrue(validate_market_fields({}))

    def test_concept_precheck_cannot_claim_compliance_verdict(self):
        self.assertEqual(validate_concept_risk_boundary({"compliance_verdict": None}), [])
        self.assertTrue(validate_concept_risk_boundary({"compliance_verdict": "pass"}))
