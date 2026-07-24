from __future__ import annotations

import unittest

from v6.engine.validators.architecture import validate_blueprint_fields, validate_foreshadow_density, validate_hook_type_alignment, validate_matrix_params, validate_opening_cross_section


class ArchitectureValidatorTests(unittest.TestCase):
    def test_blueprint_forbids_episode_scene_expansion(self):
        self.assertEqual(validate_blueprint_fields({"main_storyline": "x", "stage_turns": []}), [])
        self.assertTrue(validate_blueprint_fields({"episode_scenes": []}))

    def test_opening_cross_section_requires_goal_conflict_and_no_exposition(self):
        self.assertEqual(validate_opening_cross_section({"goal": "escape", "conflict": "door locked", "mode": "tension"}), [])
        self.assertTrue(validate_opening_cross_section({"goal": "escape", "conflict": "door locked", "theme_exposition": True}))

    def test_each_ten_episode_block_has_a_grade_foreshadow(self):
        entries = [{"setup_episode": 2, "grade": "A"}, {"setup_episode": 12, "grade": "S"}]
        self.assertEqual(validate_foreshadow_density(entries, 20), [])
        self.assertTrue(validate_foreshadow_density(entries[:1], 20))

    def test_matrix_params_have_eight_nodes_and_six_stages(self):
        valid = {"emotion_curve": list(range(8)), "act_ratio": [1] * 6, "hook_types": ["x"]}
        self.assertEqual(validate_matrix_params(valid), [])
        valid["emotion_curve"] = [1]
        self.assertTrue(validate_matrix_params(valid))

    def test_hook_types_must_come_from_brief(self):
        self.assertEqual(validate_hook_type_alignment(["x"], ["x", "y"]), [])
        self.assertTrue(validate_hook_type_alignment(["z"], ["x", "y"]))
