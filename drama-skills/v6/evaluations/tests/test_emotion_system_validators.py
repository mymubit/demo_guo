from __future__ import annotations

import unittest

from v6.engine.validators.emotion_system import (
    validate_breathing_runs,
    validate_episode_profile,
    validate_ev_platform,
    validate_payment_rising_edges,
    validate_trough_and_recovery,
)


class EmotionSystemValidatorTests(unittest.TestCase):
    def test_episode_profile_requires_indexes_and_et_minimum(self):
        nodes = [{"index": index, "value": index} for index in range(1, 9)]
        profile = {"episode": 1, "nodes": nodes, "landmarks": {"EV": 8, "ET": 1, "TP": 4}}
        self.assertEqual(validate_episode_profile(profile), [])
        profile["landmarks"]["ET"] = 3
        self.assertTrue(validate_episode_profile(profile))

    def test_ev_platform_detects_three_flat_episodes(self):
        self.assertTrue(validate_ev_platform([(1, 6), (2, 7), (3, 6)], 3, 2))
        self.assertEqual(validate_ev_platform([(1, 4), (2, 7), (3, 9)], 3, 2), [])

    def test_trough_requires_later_recovery(self):
        valid = [
            {"kind": "trough", "target_value": 3},
            {"kind": "normal", "target_value": 6},
        ]
        self.assertEqual(validate_trough_and_recovery(valid), [])
        self.assertTrue(validate_trough_and_recovery([{"kind": "normal", "target_value": 6}]))

    def test_payment_checkpoint_requires_rising_edge(self):
        valid = [
            {"episode": 1, "target_value": 4, "payment_checkpoint": False},
            {"episode": 2, "target_value": 7, "payment_checkpoint": True},
        ]
        self.assertEqual(validate_payment_rising_edges(valid), [])
        valid[1]["target_value"] = 3
        self.assertTrue(validate_payment_rising_edges(valid))

    def test_breathing_episodes_may_not_be_consecutive(self):
        valid = [{"episode": 1, "kind": "breathing"}, {"episode": 2, "kind": "normal"}]
        self.assertEqual(validate_breathing_runs(valid), [])
        valid[1]["kind"] = "breathing"
        self.assertTrue(validate_breathing_runs(valid))


if __name__ == "__main__":
    unittest.main()
