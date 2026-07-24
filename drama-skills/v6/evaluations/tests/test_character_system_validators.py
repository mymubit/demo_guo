from __future__ import annotations

import unittest

from v6.engine.validators.character_system import (
    validate_arc_ratios,
    validate_character_counts,
    validate_motivation_chain,
    validate_relationships,
)


class CharacterSystemValidatorTests(unittest.TestCase):
    def test_character_count_limits(self):
        valid = [
            {"role_type": "protagonist", "is_core": True},
            {"role_type": "supporting", "is_core": True},
            {"role_type": "supporting", "is_core": True},
        ]
        self.assertEqual(validate_character_counts(valid, 2, 2, 4), [])
        invalid = valid + [
            {"role_type": "protagonist", "is_core": True},
            {"role_type": "protagonist", "is_core": True},
        ]
        self.assertTrue(any("protagonist count" in item for item in validate_character_counts(invalid, 2, 2, 4)))

    def test_arc_ratios_accept_approximate_thirty_seventy(self):
        character = {
            "id": "hero",
            "arc": {
                "start": {"episode_ratio": 0},
                "turning_point_1": {"episode_ratio": 0.3},
                "turning_point_2": {"episode_ratio": 0.7},
                "end": {"episode_ratio": 1.0},
            },
        }
        self.assertEqual(validate_arc_ratios(character, 0.3, 0.7), [])
        character["arc"]["turning_point_1"]["episode_ratio"] = 0.65
        self.assertTrue(validate_arc_ratios(character, 0.3, 0.7))

    def test_relationships_reference_existing_characters(self):
        characters = [{"id": "a"}, {"id": "b"}]
        valid = [{"id": "a-b", "party_a": "a", "party_b": "b"}]
        self.assertEqual(validate_relationships(characters, valid, 6), [])
        invalid = valid + [{"id": "a-c", "party_a": "a", "party_b": "c"}]
        self.assertTrue(any("unknown party_b" in item for item in validate_relationships(characters, invalid, 6)))

    def test_relationships_reject_duplicate_pairs(self):
        characters = [{"id": "a"}, {"id": "b"}]
        relationships = [
            {"id": "a-b-1", "party_a": "a", "party_b": "b"},
            {"id": "a-b-2", "party_a": "b", "party_b": "a"},
        ]
        self.assertTrue(any("duplicate" in item for item in validate_relationships(characters, relationships, 6)))

    def test_motivation_chain_requires_all_fields(self):
        valid = {"id": "hero", "surface_desire": "夺回继承权", "deep_need": "学会信任", "ghost": "曾被背叛", "lie": "不能相信任何人", "flaw": "拒绝合作"}
        self.assertEqual(validate_motivation_chain(valid), [])
        valid["lie"] = ""
        self.assertTrue(validate_motivation_chain(valid))


if __name__ == "__main__":
    unittest.main()
