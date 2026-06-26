# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.drama.series_stage_utils import (
    merge_six_stage_structure,
    normalize_six_stage_structure,
    project_has_outline_structure,
)


class SeriesStageUtilsTests(TestCase):
    def test_normalize_alias_keys_and_fields(self):
        normalized = normalize_six_stage_structure(
            {
                "opening": {"episode_range": "1-10", "core_direction": "开篇方向"},
                "warming_up": {"episode_range": "11-24", "core_design": "升温设计"},
                "turning_point": {"episode_range": "25-40", "core_task": "转折任务"},
            }
        )
        self.assertEqual(normalized["opening"]["core_direction"], "开篇方向")
        self.assertEqual(normalized["warming"]["core_direction"], "升温设计")
        self.assertEqual(normalized["turning"]["core_direction"], "转折任务")

    def test_merge_prefers_nonempty_stage(self):
        merged = merge_six_stage_structure(
            {"opening": {"episode_range": "1-6"}},
            {"opening": {"episode_range": "1-10", "core_direction": "完整开篇"}},
        )
        self.assertEqual(merged["opening"]["core_direction"], "完整开篇")
        self.assertEqual(merged["opening"]["episode_range"], "1-10")

    def test_narrative_array_to_structure(self):
        normalized = normalize_six_stage_structure(
            narrative=[
                {
                    "stage_id": "S1",
                    "stage_name": "建立世界",
                    "episode_range": "1-8",
                    "core_task": "铺陈世界观",
                },
                {
                    "stage_id": "S6",
                    "stage_name": "结局",
                    "episode_range": "55-60",
                    "core_task": "收束全剧",
                },
            ]
        )
        self.assertEqual(normalized["opening"]["core_direction"], "铺陈世界观")
        self.assertEqual(normalized["ending"]["episode_range"], "55-60")

    def test_project_has_structure_requires_displayable_text(self):
        self.assertFalse(
            project_has_outline_structure({"six_stage_structure": {"opening": {"episode_range": "1-6"}}})
        )
        self.assertTrue(
            project_has_outline_structure(
                {"six_stage_structure": {"opening": {"episode_range": "1-6", "core_direction": "开篇"}}}
            )
        )
