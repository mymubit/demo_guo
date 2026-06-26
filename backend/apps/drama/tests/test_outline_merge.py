# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.agent_runtime.episode_merge import (
    merge_series_outline_artifact,
    normalize_incoming_outline_numbers,
)
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.artifact_service import get_artifact, save_artifact
from apps.creation.models import AgentExecutionRun, Project
from apps.drama.episode_outline_store import aggregate_series_outline
from apps.drama.outline_progress import summarize_series_outline_progress


class SeriesOutlineMergePersistTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.user = get_user_model().objects.create_user(phone="13900006603", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="outline-merge",
            theme="t",
            episode_count=60,
        )
        save_artifact(
            self.project,
            "series_outline",
            {
                "total_episodes": 60,
                "six_stage_structure": {"opening": {"episode_range": "1-6", "core_direction": "开篇"}},
                "episode_outlines": [
                    {"episode_num": 1, "goal_conflict": "第1集"},
                    {"episode_num": 10, "goal_conflict": "第10集"},
                ],
            },
        )
        self.agent = AgentDefinitionService.get_runnable("drama.plot-architect")
        self.run = AgentExecutionRun.objects.create(
            project=self.project,
            user=self.user,
            agent_id="drama.plot-architect",
            status=AgentExecutionRun.STATUS_RUNNING,
            batch_from=11,
            batch_to=20,
            overwrite_mode="replace",
            run_params={"episode_range": "11-20", "episode_start": 11, "episode_end": 20},
        )

    def test_merge_series_outline_keeps_previous_batches(self):
        merged = merge_series_outline_artifact(
            get_artifact(self.project, "series_outline"),
            {
                "episode_outlines": [
                    {"episode_num": 11, "goal_conflict": "第11集"},
                    {"episode_num": 20, "goal_conflict": "第20集"},
                    {"episode_num": 99, "goal_conflict": "越界"},
                ],
                "six_stage_structure": {"opening": {"episode_range": "11-20"}},
            },
            episode_from=11,
            episode_to=20,
        )
        nums = [item["episode_num"] for item in merged["episode_outlines"]]
        self.assertEqual(nums, [1, 10, 11, 20])
        self.assertEqual(
            merged["six_stage_structure"]["opening"]["episode_range"],
            "1-6",
        )

    def test_persist_series_outline_always_merges_when_existing(self):
        IndependentAgentService.persist_agent_output(
            self.project,
            self.agent,
            self.run,
            {
                "series_outline": {
                    "episode_outlines": [
                        {"episode_num": 11, "goal_conflict": "新11"},
                        {"episode_num": 12, "goal_conflict": "新12"},
                    ]
                }
            },
            prompt_version="v1",
        )
        stored = get_artifact(self.project, "series_outline") or {}
        self.assertIn("six_stage_structure", stored)
        aggregated = aggregate_series_outline(self.project)
        nums = [item["episode_num"] for item in aggregated.get("episode_outlines") or []]
        self.assertEqual(nums, [1, 10, 11, 12])

    def test_summarize_series_outline_progress_suggests_next_batch(self):
        save_artifact(
            self.project,
            "series_outline",
            {
                "total_episodes": 60,
                "episode_outlines": [{"episode_num": n, "goal_conflict": f"第{n}集"} for n in range(1, 11)],
            },
        )
        summary = summarize_series_outline_progress(self.project)
        self.assertEqual(summary["expected"], 60)
        self.assertEqual(summary["generated"], 10)
        self.assertEqual(summary["suggested_range"], "11-20")

    def test_normalize_incoming_outline_numbers_offsets_local_index(self):
        items = [
            {"episode_num": 1, "goal_conflict": "本批第1条"},
            {"episode_num": 10, "goal_conflict": "本批第10条"},
        ]
        normalized = normalize_incoming_outline_numbers(items, episode_from=11, episode_to=20)
        nums = [item["episode_num"] for item in normalized]
        self.assertEqual(nums, [11, 20])

    def test_merge_series_outline_applies_number_offset(self):
        merged = merge_series_outline_artifact(
            {
                "episode_outlines": [{"episode_num": n, "goal_conflict": f"第{n}集"} for n in range(1, 11)],
            },
            {
                "episode_outlines": [
                    {"episode_num": 1, "goal_conflict": "新11"},
                    {"episode_num": 2, "goal_conflict": "新12"},
                ],
            },
            episode_from=11,
            episode_to=20,
        )
        nums = [item["episode_num"] for item in merged["episode_outlines"]]
        self.assertIn(1, nums)
        self.assertIn(10, nums)
        self.assertIn(11, nums)
        self.assertIn(12, nums)
        by_num = {item["episode_num"]: item["goal_conflict"] for item in merged["episode_outlines"]}
        self.assertEqual(by_num[11], "新11")
        self.assertEqual(by_num[12], "新12")
