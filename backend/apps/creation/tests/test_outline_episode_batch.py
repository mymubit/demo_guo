# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.creation.models import Project
from apps.creation.agent_runtime.episode_merge import (
    filter_episodes_by_range,
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
