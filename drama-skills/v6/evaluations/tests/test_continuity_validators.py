from __future__ import annotations

import unittest

from v6.engine.validators.continuity import (
    validate_checkpoint_binding,
    validate_checkpoint_coverage,
    validate_episode_scope,
    validate_previous_episode,
)


class ContinuityValidatorTests(unittest.TestCase):
    def test_episode_must_be_inside_explicit_range(self):
        self.assertEqual(validate_episode_scope(8, [8, 9]), [])
        self.assertTrue(validate_episode_scope(8, []))
        self.assertTrue(validate_episode_scope(10, [8, 9]))

    def test_previous_episode_must_be_immediate_predecessor(self):
        self.assertEqual(validate_previous_episode(8, {"episode": 7}), [])
        self.assertTrue(validate_previous_episode(8, {"episode": 6}))
        self.assertTrue(validate_previous_episode(8, None))

    def test_first_episode_has_no_predecessor(self):
        self.assertEqual(validate_previous_episode(1, None), [])
        self.assertTrue(validate_previous_episode(1, {"episode": 0}))

    def test_checkpoint_binds_to_completed_episode(self):
        self.assertEqual(validate_checkpoint_binding(8, {"episode": 8}), [])
        self.assertTrue(validate_checkpoint_binding(8, {"episode": 7}))

    def test_every_completed_episode_has_exactly_scoped_checkpoint(self):
        self.assertEqual(validate_checkpoint_coverage([8, 9], [{"episode": 8}, {"episode": 9}]), [])
        self.assertTrue(validate_checkpoint_coverage([8, 9], [{"episode": 8}]))
        self.assertTrue(validate_checkpoint_coverage([8], [{"episode": 8}, {"episode": 9}]))
