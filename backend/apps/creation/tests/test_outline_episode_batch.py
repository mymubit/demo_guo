# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.creation.models import Project
from apps.creation.agent_runtime.episode_merge import (
    filter_episodes_by_range,
    merge_episode_designs_by_number,
    merge_episode_outlines_by_number,
    merge_episodes_by_number,
)
from apps.creation.workspace.workspace_editor import compute_outline_batch_range


class OutlineEpisodeBatchTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(phone="13900006602", password="test-pass-123")

    def test_merge_episodes_by_number_clamps_to_requested_range(self):
        existing = {"episodes": [{"episodeNumber": 1, "oneLineSummary": "旧第1集"}]}
        incoming = [
            {"episodeNumber": 1, "oneLineSummary": "新第1集"},
            {"episodeNumber": 2, "oneLineSummary": "第2集"},
            {"episodeNumber": 23, "oneLineSummary": "第23集"},
        ]
        merged = merge_episodes_by_number(
            existing,
            incoming,
            episode_from=1,
            episode_to=1,
        )
        nums = [e["episodeNumber"] for e in merged["episodes"]]
        self.assertEqual(nums, [1])
        self.assertEqual(merged["episodes"][0]["oneLineSummary"], "新第1集")

    def test_filter_episodes_by_range(self):
        rows = [
            {"episodeNumber": 0},
            {"episodeNumber": 1, "oneLineSummary": "a"},
            {"episodeNumber": 3, "oneLineSummary": "b"},
        ]
        kept = filter_episodes_by_range(rows, 1, 2)
        self.assertEqual([e["episodeNumber"] for e in kept], [1])

    def test_merge_episode_designs_by_number_keeps_other_batches(self):
        existing = {
            "episode_narrative_designs": [
                {"episode_id": "E001", "narrative_focus": "第一集"},
                {"episode_id": "E005", "narrative_focus": "第五集"},
            ],
            "target_episode_range": "E001-E005",
        }
        incoming = [
            {"episode_id": "E006", "narrative_focus": "第六集"},
            {"episode_id": "E010", "narrative_focus": "第十集"},
            {"episode_id": "E099", "narrative_focus": "越界"},
        ]
        merged = merge_episode_designs_by_number(
            existing,
            incoming,
            episode_from=6,
            episode_to=10,
        )
        nums = [item["episode_id"] for item in merged["episode_narrative_designs"]]
        self.assertEqual(nums, ["E001", "E005", "E006", "E010"])
        self.assertEqual(merged["target_episode_range"], "E001-E010")

    def test_compute_outline_batch_range_skips_placeholder_episodes(self):
        project = Project.objects.create(
            user=self.user,
            title="batch-test",
            theme="t",
            episode_count=40,
        )
        from apps.creation.artifact_service import save_artifact

        save_artifact(
            project,
            "series_outline",
            {
                "episodes": [
                    {"episodeNumber": 1, "oneLineSummary": ""},
                    {"episodeNumber": 2, "oneLineSummary": "已有第2集"},
                ]
            },
        )
        o_from, o_to, _ = compute_outline_batch_range(
            project,
            block_from=1,
            block_to=4,
            batch_size=1,
        )
        self.assertEqual((o_from, o_to), (1, 1))

    def test_merge_episode_outlines_by_number_keeps_other_batches(self):
        existing = {
            "episode_outlines": [
                {"episode_num": 1, "goal_conflict": "第一集"},
                {"episode_num": 10, "goal_conflict": "第十集"},
            ],
            "six_stage_structure": {"opening": {"episode_range": "1-6"}},
        }
        incoming = [
            {"episode_num": 11, "goal_conflict": "第十一集"},
            {"episode_num": 20, "goal_conflict": "第二十集"},
            {"episode_num": 99, "goal_conflict": "越界"},
        ]
        merged = merge_episode_outlines_by_number(
            existing,
            incoming,
            episode_from=11,
            episode_to=20,
        )
        nums = [item["episode_num"] for item in merged["episode_outlines"]]
        self.assertEqual(nums, [1, 10, 11, 20])
        self.assertEqual(merged["six_stage_structure"]["opening"]["episode_range"], "1-6")
        self.assertEqual(merged["target_episode_range"], "E001-E020")
