from __future__ import annotations

import unittest

from v6.engine.validators.scene_system import (
    validate_dialogue_speakers,
    validate_information_gaps,
    validate_scene_power_shift,
    validate_scene_value_changes,
    validate_segments,
)


class SceneSystemValidatorTests(unittest.TestCase):
    def test_segments_require_four_kinds_and_total_one(self):
        valid = [
            {"kind": "hook", "ratio": 0.1}, {"kind": "situation", "ratio": 0.3},
            {"kind": "escalation", "ratio": 0.4}, {"kind": "cliffhanger", "ratio": 0.2},
        ]
        self.assertEqual(validate_segments(valid), [])
        valid[3]["ratio"] = 0.3
        self.assertTrue(validate_segments(valid))

    def test_information_knowers_may_not_overlap(self):
        valid = [{"id": "i1", "knowers": ["a"], "nonknowers": ["b"]}]
        self.assertEqual(validate_information_gaps(valid), [])
        valid[0]["nonknowers"].append("a")
        self.assertTrue(validate_information_gaps(valid))

    def test_scene_requires_value_change(self):
        self.assertEqual(validate_scene_value_changes([{"id": "s1", "value_before": "loss", "value_after": "gain"}]), [])
        self.assertTrue(validate_scene_value_changes([{"id": "s1", "value_before": "loss", "value_after": "loss"}]))

    def test_dialogue_speaker_must_exist(self):
        scenes = [{"id": "s1", "dialogue": [{"speaker": "a"}]}]
        self.assertEqual(validate_dialogue_speakers(scenes, ["a"]), [])
        self.assertTrue(validate_dialogue_speakers(scenes, ["b"]))

    def test_dialogue_requires_observable_power_shift(self):
        valid = [{"id": "s1", "dialogue": [{"power_before": -1, "power_after": 1}]}]
        self.assertEqual(validate_scene_power_shift(valid), [])
        valid[0]["dialogue"][0]["power_after"] = -1
        self.assertTrue(validate_scene_power_shift(valid))


if __name__ == "__main__":
    unittest.main()
