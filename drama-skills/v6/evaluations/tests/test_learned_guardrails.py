from __future__ import annotations

import unittest

from v6.engine.validators.learned_guardrails import validate_breathing_density, validate_crisis_rhythm, validate_identity_reveal, validate_monologue_run, validate_progressive_beats, validate_revenge_opening, validate_structured_output


class LearnedGuardrailTests(unittest.TestCase):
    def test_revenge_opening_boundary(self):
        self.assertEqual(validate_revenge_opening(30), [])
        self.assertTrue(validate_revenge_opening(30.1))

    def test_monologue_maximum_three_lines(self):
        self.assertEqual(validate_monologue_run(3), [])
        self.assertTrue(validate_monologue_run(4))

    def test_identity_reveal_exact_boundaries(self):
        self.assertEqual(validate_identity_reveal(5, 3, 0.55), [])
        self.assertEqual(validate_identity_reveal(5, 3, 0.75), [])
        self.assertTrue(validate_identity_reveal(4, 4, 0.76))

    def test_progressive_beats_require_ratio_and_state_change(self):
        valid = [{"kind": "progressive", "changes": ["goal"]} for _ in range(3)] + [{"kind": "pause"} for _ in range(2)]
        self.assertEqual(validate_progressive_beats(valid), [])
        valid[0]["changes"] = []
        self.assertTrue(validate_progressive_beats(valid))

    def test_breathing_episode_rolling_window(self):
        self.assertEqual(validate_breathing_density([1, 11]), [])
        self.assertTrue(validate_breathing_density([1, 10]))
        self.assertTrue(validate_breathing_density([4, 5]))

    def test_crisis_episode_requires_tight_heavy(self):
        self.assertEqual(validate_crisis_rhythm("identity-reveal", "tight", "heavy"), [])
        self.assertTrue(validate_crisis_rhythm("identity-reveal", "medium", "heavy"))

    def test_structured_output_rejects_metadata_and_enum_synonyms(self):
        self.assertEqual(validate_structured_output({"status": "active"}, {"status": {"active", "inactive"}}), [])
        self.assertTrue(validate_structured_output({"schema_version": 1}, {}))
        self.assertTrue(validate_structured_output({"status": "enabled"}, {"status": {"active", "inactive"}}))
