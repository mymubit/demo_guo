from __future__ import annotations

import unittest

from v6.engine.validators.production import validate_budget_boundary, validate_high_complexity_alternatives, validate_release_evidence, validate_release_policy


class ProductionValidatorTests(unittest.TestCase):
    def test_high_complexity_requires_alternative(self):
        self.assertEqual(validate_high_complexity_alternatives([{"scene_id": "s1", "complexity": "high", "alternatives": [{}]}]), [])
        self.assertTrue(validate_high_complexity_alternatives([{"scene_id": "s1", "complexity": "high", "alternatives": []}]))

    def test_unquoted_budget_must_remain_a_band(self):
        self.assertEqual(validate_budget_boundary(False, {"mode": "band"}), [])
        self.assertTrue(validate_budget_boundary(False, {"mode": "amount", "amount": 100}))

    def test_amount_requires_provenance(self):
        valid = {"mode": "amount", "currency": "CNY", "region": "Shanghai", "price_version": "2026-07", "excluded_items": []}
        self.assertEqual(validate_budget_boundary(True, valid), [])
        del valid["region"]
        self.assertTrue(validate_budget_boundary(True, valid))

    def test_unverified_policy_blocks_ready_status(self):
        self.assertTrue(validate_release_policy({"policy_status": "expired", "release_ready": True}))
        self.assertEqual(validate_release_policy({"policy_status": "expired", "release_ready": False}), [])

    def test_release_ready_requires_all_evidence(self):
        valid = {key: True for key in ["ai_content_labeling", "filing_materials", "title_check", "rights_authorization", "quality_report", "compliance_report"]}
        valid["release_ready"] = True
        self.assertEqual(validate_release_evidence(valid), [])
        valid["rights_authorization"] = False
        self.assertTrue(validate_release_evidence(valid))
