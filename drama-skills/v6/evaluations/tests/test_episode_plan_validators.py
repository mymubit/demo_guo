from __future__ import annotations

import unittest

from v6.engine.validators.episode_plan import (
    allocate_stages,
    validate_conflict_type_coverage,
    validate_confrontation,
    validate_foreshadow_tracking,
    validate_global_structure_readonly,
    validate_required_card_content,
    validate_rhythm_run,
    validate_hook_grade,
    validate_hook_count,
    validate_payment_payoff,
    validate_payment_window,
    validate_episode_context,
    validate_foreshadow_payoff_delay,
    validate_foreshadow_type,
    validate_overdue_foreshadow_checkpoint,
)


class EpisodePlanValidatorTests(unittest.TestCase):
    def test_global_structure_readonly_accepts_scoped_episode_changes(self):
        self.assertEqual(
            validate_global_structure_readonly(["episode_plan.episodes.8", "episode_plan.episodes.9"]), []
        )

    def test_global_structure_readonly_rejects_story_bible_change(self):
        errors = validate_global_structure_readonly(["story_bible.major_reversal_positions.0"])
        self.assertEqual(len(errors), 1)

    def test_required_card_content_rejects_missing_and_empty_fields(self):
        errors = validate_required_card_content([{"episode": 8, "title": ""}])
        self.assertTrue(any("missing fields" in error for error in errors))
        self.assertTrue(any("empty field title" in error for error in errors))

    def test_foreshadow_tracking_requires_setup_and_payoff(self):
        errors = validate_foreshadow_tracking(
            [{"episode": 8, "foreshadowing": {"entries": [{"setup_episode": 8}]}}]
        )
        self.assertEqual(errors, ["episode 8 foreshadow 0: missing payoff_episode"])

    def test_rhythm_run_rejects_third_identical_tag(self):
        cards = [
            {"episode": 8, "rhythm_tag": "tight-heavy"},
            {"episode": 9, "rhythm_tag": "tight-heavy"},
            {"episode": 10, "rhythm_tag": "tight-heavy"},
        ]
        self.assertEqual(len(validate_rhythm_run(cards, maximum_run=2)), 1)

    def test_rhythm_run_accepts_variation(self):
        cards = [
            {"episode": 8, "rhythm_tag": "tight-heavy"},
            {"episode": 9, "rhythm_tag": "tight-heavy"},
            {"episode": 10, "rhythm_tag": "medium-light"},
        ]
        self.assertEqual(validate_rhythm_run(cards, maximum_run=2), [])

    def test_hook_grade_uses_canonical_order(self):
        self.assertEqual(validate_hook_grade("A", "B"), [])
        self.assertEqual(len(validate_hook_grade("C", "B")), 1)
        self.assertEqual(len(validate_hook_grade("X", "B")), 1)

    def test_hook_count_uses_minimum_grade(self):
        self.assertEqual(validate_hook_count(["B", "A", "S"], 3, "B"), [])
        self.assertEqual(len(validate_hook_count(["C", "B"], 2, "B")), 1)

    def test_conflict_type_coverage(self):
        self.assertEqual(validate_conflict_type_coverage(["external", "interpersonal", "internal"], 3), [])
        self.assertEqual(len(validate_conflict_type_coverage(["external", "internal"], 3)), 1)

    def test_confrontation_requires_five_elements(self):
        valid = {
            "power_balance": "反派掌握账本",
            "stated_demand": "女主退出继承",
            "real_intent": "逼女主承认账本有效",
            "power_shift": "女主发现纸张年份异常",
            "ending_value_change": "账本从证据变成反派弱点",
        }
        self.assertEqual(validate_confrontation(valid), [])
        self.assertEqual(len(validate_confrontation({"power_balance": "反派占优"})), 1)

    def test_payment_windows(self):
        self.assertEqual(validate_payment_window(4, 3, 5, "first"), [])
        self.assertEqual(len(validate_payment_window(8, 3, 5, "first")), 1)

    def test_payment_payoff_deadline(self):
        self.assertEqual(validate_payment_payoff(4, 5, 1), [])
        self.assertEqual(len(validate_payment_payoff(4, 7, 1)), 1)

    def test_largest_remainder_stage_allocation_preserves_total(self):
        self.assertEqual(allocate_stages(60, [0.10, 0.20, 0.20, 0.20, 0.15, 0.15]), [6, 12, 12, 12, 9, 9])
        compact = allocate_stages(10, [0.10, 0.20, 0.20, 0.20, 0.15, 0.15])
        self.assertEqual(sum(compact), 10)
        self.assertTrue(all(value >= 1 for value in compact))

    def test_stage_allocation_rejects_too_few_episodes(self):
        with self.assertRaises(ValueError):
            allocate_stages(5, [1, 1, 1, 1, 1, 1])

    def test_foreshadow_type_is_canonical(self):
        self.assertEqual(validate_foreshadow_type("identity"), [])
        self.assertEqual(len(validate_foreshadow_type("身份")), 1)

    def test_foreshadow_payoff_deadline(self):
        self.assertEqual(validate_foreshadow_payoff_delay(8, 10, 3), [])
        self.assertEqual(len(validate_foreshadow_payoff_delay(8, 12, 3)), 1)

    def test_episode_context_is_allowlisted(self):
        context = {
            "previous_episode": {},
            "memory_checkpoint": {},
            "current_episode_card": {},
            "unresolved_foreshadowing": [],
            "active_global_constraints": [],
        }
        self.assertEqual(validate_episode_context(context), [])
        context["entire_script"] = {}
        self.assertEqual(len(validate_episode_context(context)), 1)

    def test_overdue_foreshadow_remains_in_checkpoint(self):
        self.assertEqual(validate_overdue_foreshadow_checkpoint(["F1"], ["F1", "F2"]), [])
        self.assertEqual(len(validate_overdue_foreshadow_checkpoint(["F1", "F3"], ["F1"])), 1)


if __name__ == "__main__":
    unittest.main()
