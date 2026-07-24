from __future__ import annotations

import unittest

from v6.engine.validators.world_system import (
    validate_condition_consequence_consistency,
    validate_registered_rule_usage,
    validate_reveal_layer_count,
    validate_rule_choice_coverage,
    validate_world_references,
)


class WorldSystemValidatorTests(unittest.TestCase):
    def test_world_references_accept_known_rules(self):
        world = {
            "rules": [{"id": "world-rule-a"}],
            "power_structure": {"loopholes": [{"id": "loophole-a", "rule_id": "world-rule-a"}]},
            "reveal_plan": [{"rule_id": "world-rule-a"}],
        }
        self.assertEqual(validate_world_references(world), [])
        world["reveal_plan"][0]["rule_id"] = "world-rule-missing"
        self.assertTrue(validate_world_references(world))

    def test_reveal_layer_limit(self):
        valid = [{"episode": 1, "layer": "evidence"}]
        self.assertEqual(validate_reveal_layer_count(valid, 1), [])
        invalid = valid + [{"episode": 1, "layer": "voting"}]
        self.assertEqual(len(validate_reveal_layer_count(invalid, 1)), 1)

    def test_same_condition_requires_same_consequence(self):
        valid = [
            {"rule_id": "r1", "condition_key": "fake-evidence", "consequence_key": "suspend"},
            {"rule_id": "r1", "condition_key": "fake-evidence", "consequence_key": "suspend"},
        ]
        self.assertEqual(validate_condition_consequence_consistency(valid), [])
        valid[1]["consequence_key"] = "approve"
        self.assertEqual(len(validate_condition_consequence_consistency(valid)), 1)

    def test_downstream_may_only_use_registered_rules(self):
        self.assertEqual(validate_registered_rule_usage(["r1", "r2"], ["r2"]), [])
        self.assertTrue(validate_registered_rule_usage(["r1"], ["r2"]))

    def test_every_rule_drives_a_planned_choice(self):
        world = {
            "rules": [{"id": "r1"}, {"id": "r2"}],
            "reveal_plan": [{"rule_id": "r1", "affected_choice": "主角提交证据"}],
        }
        self.assertTrue(validate_rule_choice_coverage(world))
        world["reveal_plan"].append({"rule_id": "r2", "affected_choice": "主角承担代价"})
        self.assertEqual(validate_rule_choice_coverage(world), [])


if __name__ == "__main__":
    unittest.main()
