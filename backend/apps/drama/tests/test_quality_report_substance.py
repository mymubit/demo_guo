# backend/apps/drama/tests/test_quality_report_substance.py
from django.test import SimpleTestCase, override_settings

from apps.drama.services.artifact_normalize import (
    compliance_report_too_thin,
    normalize_compliance_report,
)
from apps.drama.tests.helpers import SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class SubstanceGateTests(SimpleTestCase):
    def test_compliance_fail_without_titled_blocking_is_thin(self) -> None:
        raw = {
            "drama_title": "t",
            "overall_result": "不通过",
            "blocking_issues": [{"description": ""}],
            "risk_items": [],
        }
        out = normalize_compliance_report(raw, {})
        self.assertTrue(compliance_report_too_thin(out))

    def test_empty_suggestion_remains_thin(self) -> None:
        """normalize 不再补默认 suggestion；空建议仍视为过薄。"""
        raw = {
            "drama_title": "t",
            "overall_result": "通过",
            "blocking_issues": [],
            "risk_items": [
                {
                    "type": "p2",
                    "description": "建议在结局部分增加反派受到明确法律惩罚的描写，以强化正义收束。",
                    "suggestion": "",
                }
            ],
        }
        out = normalize_compliance_report(raw, {})
        self.assertEqual(out["risk_items"][0]["suggestion"], "")
        self.assertTrue(compliance_report_too_thin(out))

    def test_compliance_pass_with_detailed_p2_ok(self) -> None:
        raw = {
            "drama_title": "t",
            "overall_result": "通过",
            "blocking_issues": [],
            "risk_items": [
                {
                    "type": "p2",
                    "description": "结尾反派缺少明确法律收束，观众易不满",
                    "suggestion": "在终章增加官府处置或判刑场面",
                }
            ],
        }
        out = normalize_compliance_report(raw, {})
        self.assertFalse(compliance_report_too_thin(out))
