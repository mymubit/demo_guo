# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.artifact_service import get_artifact, get_fusion_meta_payload, save_artifact
from apps.creation.models import AgentExecutionRun, Project
from apps.drama.episode_outline_store import (
    EPISODE_OUTLINE_ARTIFACT_KEY,
    OUTLINE_MODE_EPISODES_ONLY,
    OUTLINE_MODE_STRUCTURE_ONLY,
    aggregate_series_outline,
    persist_series_outline_output,
    resolve_outline_mode,
)
from apps.drama.models import DramaEpisodeArtifact
from apps.drama.outline_progress import summarize_series_outline_progress


class EpisodeOutlineStoreTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.user = get_user_model().objects.create_user(phone="13900006604", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="per-ep-outline",
            theme="t",
            episode_count=60,
        )
        self.agent = AgentDefinitionService.get_runnable("drama.plot-architect")

    def test_persist_writes_each_episode_row(self):
        persist_series_outline_output(
            self.project,
            {
                "total_episodes": 60,
                "six_stage_structure": {"opening": {"episode_range": "1-6"}},
                "episode_outlines": [
                    {"episode_num": 1, "goal_conflict": "第1集"},
                    {"episode_num": 10, "goal_conflict": "第10集"},
                ],
            },
            agent_id="drama.plot-architect",
            run_id="run-1",
            episode_from=1,
            episode_to=10,
        )
        rows = DramaEpisodeArtifact.objects.filter(
            project=self.project,
            artifact_key=EPISODE_OUTLINE_ARTIFACT_KEY,
        ).order_by("episode_number")
        self.assertEqual(rows.count(), 2)
        self.assertEqual(rows[0].episode_number, 1)
        meta = get_fusion_meta_payload(self.project, "series_outline")
        self.assertIn("six_stage_structure", meta)
        self.assertNotIn("episode_outlines", meta)

    def test_second_batch_does_not_remove_first_batch(self):
        persist_series_outline_output(
            self.project,
            {"episode_outlines": [{"episode_num": n, "goal_conflict": f"第{n}集"} for n in range(1, 11)]},
            agent_id="drama.plot-architect",
            run_id="run-1",
            episode_from=1,
            episode_to=10,
        )
        persist_series_outline_output(
            self.project,
            {
                "episode_outlines": [
                    {"episode_num": 1, "goal_conflict": "错标1"},
                    {"episode_num": 2, "goal_conflict": "错标2"},
                ],
            },
            agent_id="drama.plot-architect",
            run_id="run-2",
            episode_from=11,
            episode_to=20,
        )
        aggregated = aggregate_series_outline(self.project)
        nums = [item["episode_num"] for item in aggregated["episode_outlines"]]
        self.assertEqual(nums, list(range(1, 13)))
        by_num = {item["episode_num"]: item["goal_conflict"] for item in aggregated["episode_outlines"]}
        self.assertEqual(by_num[1], "第1集")
        self.assertEqual(by_num[11], "错标1")
        self.assertEqual(by_num[12], "错标2")

    def test_legacy_backfill_on_aggregate(self):
        save_artifact(
            self.project,
            "series_outline",
            {
                "six_stage_structure": {"opening": {"episode_range": "1-6"}},
                "episode_outlines": [
                    {"episode_num": 3, "goal_conflict": "legacy3"},
                    {"episode_num": 4, "goal_conflict": "legacy4"},
                ],
            },
        )
        aggregated = aggregate_series_outline(self.project)
        nums = [item["episode_num"] for item in aggregated["episode_outlines"]]
        self.assertEqual(nums, [3, 4])
        self.assertTrue(
            DramaEpisodeArtifact.objects.filter(
                project=self.project,
                artifact_key=EPISODE_OUTLINE_ARTIFACT_KEY,
            ).exists()
        )

    def test_progress_reads_from_episode_store(self):
        persist_series_outline_output(
            self.project,
            {"episode_outlines": [{"episode_num": n, "goal_conflict": f"第{n}集"} for n in range(1, 11)]},
            agent_id="drama.plot-architect",
            run_id="run-1",
            episode_from=1,
            episode_to=10,
        )
        summary = summarize_series_outline_progress(self.project)
        self.assertEqual(summary["generated"], 10)
        self.assertEqual(summary["suggested_range"], "11-20")

    def test_persist_schema_episodes_format_with_core_event(self):
        persist_series_outline_output(
            self.project,
            {
                "episodes": [
                    {"episode": 11, "core_event": "第11集核心事件", "title": "转折前夜"},
                    {"episode": 12, "core_event": "第12集核心事件"},
                ],
            },
            agent_id="drama.plot-architect",
            run_id="run-schema",
            episode_from=11,
            episode_to=20,
        )
        aggregated = aggregate_series_outline(self.project)
        nums = [item.get("episode_num") or item.get("episode") for item in aggregated["episode_outlines"]]
        self.assertEqual(sorted(n for n in nums if n), [11, 12])

    def test_batch_persist_without_episodes_raises(self):
        with self.assertRaises(ValueError):
            persist_series_outline_output(
                self.project,
                {"six_stage_structure": {"opening": {"episode_range": "11-20"}}},
                agent_id="drama.plot-architect",
                run_id="run-empty",
                episode_from=11,
                episode_to=20,
            )

    def test_independent_persist_uses_episode_store(self):
        run = AgentExecutionRun.objects.create(
            project=self.project,
            user=self.user,
            agent_id="drama.plot-architect",
            status=AgentExecutionRun.STATUS_RUNNING,
            batch_from=1,
            batch_to=2,
            run_params={"episode_range": "1-2"},
        )
        IndependentAgentService.persist_agent_output(
            self.project,
            self.agent,
            run,
            {
                "series_outline": {
                    "episode_outlines": [
                        {"episode_num": 1, "goal_conflict": "A"},
                        {"episode_num": 2, "goal_conflict": "B"},
                    ],
                }
            },
            prompt_version="v1",
        )
        self.assertEqual(
            DramaEpisodeArtifact.objects.filter(
                project=self.project,
                artifact_key=EPISODE_OUTLINE_ARTIFACT_KEY,
            ).count(),
            2,
        )

    def test_episodes_only_ignores_incoming_structure(self):
        persist_series_outline_output(
            self.project,
            {
                "six_stage_structure": {"opening": {"episode_range": "1-6"}},
                "episode_outlines": [{"episode_num": n, "goal_conflict": f"第{n}集"} for n in range(1, 11)],
            },
            agent_id="drama.plot-architect",
            run_id="run-1",
            episode_from=1,
            episode_to=10,
        )
        persist_series_outline_output(
            self.project,
            {
                "six_stage_structure": {"opening": {"episode_range": "11-20", "summary": "应被忽略"}},
                "foreshadowing_list": [{"content": "新伏笔应被忽略"}],
                "episode_outlines": [{"episode_num": 11, "goal_conflict": "第11集"}],
            },
            agent_id="drama.plot-architect",
            run_id="run-2",
            episode_from=11,
            episode_to=20,
            run_params={"outline_mode": OUTLINE_MODE_EPISODES_ONLY},
        )
        meta = get_fusion_meta_payload(self.project, "series_outline")
        self.assertEqual(meta["six_stage_structure"]["opening"]["episode_range"], "1-6")
        self.assertNotIn("foreshadowing_list", meta)

    def test_structure_only_writes_meta_without_episodes(self):
        persist_series_outline_output(
            self.project,
            {"episode_outlines": [{"episode_num": 1, "goal_conflict": "已有"}]},
            agent_id="drama.plot-architect",
            run_id="run-ep",
            episode_from=1,
            episode_to=1,
        )
        persist_series_outline_output(
            self.project,
            {
                "six_stage_structure": {"opening": {"episode_range": "1-10", "summary": "开篇"}},
                "foreshadowing_list": [{"content": "伏笔A", "buried": 3, "payoff": 20}],
            },
            agent_id="drama.plot-architect",
            run_id="run-struct",
            run_params={"outline_mode": OUTLINE_MODE_STRUCTURE_ONLY},
        )
        self.assertEqual(
            DramaEpisodeArtifact.objects.filter(
                project=self.project,
                artifact_key=EPISODE_OUTLINE_ARTIFACT_KEY,
            ).count(),
            1,
        )
        meta = get_fusion_meta_payload(self.project, "series_outline")
        self.assertIn("six_stage_structure", meta)
        self.assertEqual(len(meta.get("foreshadowing_list") or []), 1)
        summary = summarize_series_outline_progress(self.project)
        self.assertTrue(summary["has_structure"])

    def test_resolve_outline_mode_defaults(self):
        meta = {"six_stage_structure": {"opening": {"episode_range": "1-6"}}}
        self.assertEqual(
            resolve_outline_mode(None, episode_from=11, existing_meta=meta),
            OUTLINE_MODE_EPISODES_ONLY,
        )
        self.assertEqual(
            resolve_outline_mode(None, episode_from=1, existing_meta={}),
            "full",
        )
