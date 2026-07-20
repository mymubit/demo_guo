# -*- coding: utf-8 -*-
from django.test import SimpleTestCase, override_settings

from apps.drama.services.skill_ops_service import _classify, load_eval_summary
from apps.drama.tests.helpers import SKILLS_ROOT


class _FakeLog:
    def __init__(self, *, purpose="", error_message="", role="", status="error"):
        self.purpose = purpose
        self.error_message = error_message
        self.role = role
        self.status = status


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class SkillOpsServiceTests(SimpleTestCase):
    def test_load_eval_summary_from_skills(self):
        summary = load_eval_summary()
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertIn("pass_rate", summary)
        self.assertGreaterEqual(int(summary.get("total") or 0), 1)

    def test_classify_filters_noise(self):
        self.assertEqual(
            _classify(_FakeLog(purpose="connectivity_test", role="admin.connectivity-test")),
            "infra",
        )
        self.assertEqual(
            _classify(
                _FakeLog(error_message="HTTPSConnectionPool Read timed out. (read timeout=300)")
            ),
            "infra",
        )
        self.assertEqual(
            _classify(
                _FakeLog(
                    error_message="InvalidParameter: json_object is not supported by this model"
                )
            ),
            "provider_config",
        )
        self.assertEqual(
            _classify(_FakeLog(purpose="artifact_generation_json_repair")),
            "skill_structure",
        )
        self.assertIsNone(
            _classify(_FakeLog(purpose="artifact_generation", error_message="unknown boom"))
        )
