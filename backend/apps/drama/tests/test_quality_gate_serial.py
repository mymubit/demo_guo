# -*- coding: utf-8 -*-
from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from apps.drama.services.quality_gate import (
    prefer_parallel_quality_judges,
    quality_gate_passed,
    quality_score_meets_threshold,
    skipped_compliance_report,
)
from apps.drama.tests.helpers import FIXTURES, SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, DRAMA_QUALITY_JUDGES_PARALLEL=False)
class QualityGateSerialHelpersTests(SimpleTestCase):
    def test_score_threshold_helpers(self) -> None:
        high = dict(FIXTURES["quality_report"])
        high["overall_score"] = 82
        low = dict(FIXTURES["quality_report"])
        low["overall_score"] = 60
        self.assertTrue(quality_score_meets_threshold(high))
        self.assertFalse(quality_score_meets_threshold(low))
        self.assertTrue(quality_gate_passed(high, FIXTURES["compliance_report"]))
        self.assertFalse(quality_gate_passed(low, FIXTURES["compliance_report"]))

    def test_prefer_parallel_defaults_false(self) -> None:
        self.assertFalse(prefer_parallel_quality_judges())
        self.assertTrue(
            prefer_parallel_quality_judges(
                request_payload={"parallel_quality_judges": True}
            )
        )
        self.assertTrue(
            prefer_parallel_quality_judges(
                project_settings={
                    "creation_preferences": {"parallel_quality_judges": True}
                }
            )
        )

    def test_skipped_compliance_report_shape(self) -> None:
        report = skipped_compliance_report(overall_score=60, threshold=75)
        self.assertEqual(report["overall_result"], "风险")
        self.assertEqual(report["blocking_issues"], [])
        self.assertIn("跳过合规", report["risk_items"][0]["description"])
