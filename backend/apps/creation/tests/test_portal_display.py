# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from apps.creation.display.portal_display import (
    portal_execution_run,
    portal_gate_log,
    portal_sanitize_character_bible_view,
    portal_sanitize_review_block,
    portal_sanitize_reversal,
    portal_sanitize_structure_plan_view,
    portal_strip_agent_block,
)


class PortalDisplayTests(SimpleTestCase):
    def test_portal_gate_log_passed_strips_issues(self):
        log = portal_gate_log({"passed": True, "issues": ["不应展示"], "checker": "sub-world"})
        self.assertEqual(log, {"passed": True, "skipped": False})

    def test_portal_gate_log_failed_caps_issues(self):
        issues = [f"issue-{i}" for i in range(10)]
        log = portal_gate_log({"passed": False, "issues": issues})
        self.assertEqual(len(log["issues"]), 5)

    def test_portal_sanitize_reversal_strips_weapon_fields(self):
        rev = portal_sanitize_reversal(
            {
                "episodeNumber": 3,
                "description": "反转",
                "techniqueCode": "H-01",
                "patternName": "身份揭晓",
            }
        )
        self.assertEqual(rev["episodeNumber"], 3)
        self.assertNotIn("techniqueCode", rev)
        self.assertNotIn("patternName", rev)

    def test_portal_sanitize_structure_plan_view(self):
        view = portal_sanitize_structure_plan_view(
            {
                "referenceLibrary": {"hookTypes": [{"code": "H1"}]},
                "worldValidationLog": {"passed": True, "checker": "x"},
                "keyReversalPoints": [{"episodeNumber": 1, "techniqueCode": "T1"}],
                "rhythmCurve": [{"episodeRange": "1-5", "suggestedHooks": [{"code": "H1"}]}],
            }
        )
        self.assertNotIn("referenceLibrary", view)
        self.assertEqual(view["worldValidationLog"], {"passed": True, "skipped": False})
        self.assertNotIn("techniqueCode", view["keyReversalPoints"][0])
        self.assertNotIn("suggestedHooks", view["rhythmCurve"][0])

    def test_portal_sanitize_character_bible_view(self):
        view = portal_sanitize_character_bible_view(
            {
                "summary": "总述",
                "archetypeCodes": ["hero"],
                "archetypeIndex": {"hero": {}},
                "creativeDna": {"antiClicheElements": ["x"]},
                "characters": [{"name": "A", "archetypeCode": "hero"}],
            }
        )
        self.assertNotIn("archetypeCodes", view)
        self.assertNotIn("archetypeIndex", view)
        self.assertNotIn("creativeDna", view)
        self.assertNotIn("archetypeCode", view["characters"][0])

    def test_portal_strip_agent_block(self):
        block = portal_strip_agent_block(
            {
                "passed": True,
                "executionTrace": [{"id": "x"}],
                "executionRun": {"duration_ms": 88000, "execution_trace": [{"id": "y"}]},
            }
        )
        self.assertNotIn("executionTrace", block)
        self.assertNotIn("executionRun", block)
        self.assertEqual(block["durationMs"], 88000)

        compact = portal_execution_run({"duration_ms": 1200, "sub_skills": []})
        self.assertEqual(compact, {"duration_ms": 1200})

    def test_portal_sanitize_review_block(self):
        block = portal_sanitize_review_block(
            {
                "passed": False,
                "plotStructure": {
                    "passed": False,
                    "assessments": ["内部条目"],
                    "issues": ["用户可读问题"],
                },
                "qualityGuard": {
                    "passed": False,
                    "assessments": ["扣分项"],
                    "issues": ["套话偏多"],
                    "totalDeductionPoints": 12,
                    "predictedScore": 70,
                },
            }
        )
        self.assertNotIn("assessments", block["plotStructure"])
        self.assertEqual(block["plotStructure"]["issues"], ["用户可读问题"])
        self.assertNotIn("totalDeductionPoints", block["qualityGuard"])
        self.assertNotIn("predictedScore", block["qualityGuard"])
