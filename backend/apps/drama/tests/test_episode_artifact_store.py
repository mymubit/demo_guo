# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.agent.definition_service import AgentDefinitionService
from apps.creation.agent_runtime.independent_service import IndependentAgentService
from apps.creation.artifact_service import get_artifact, save_artifact
from apps.creation.models import AgentExecutionRun, Project
from apps.drama.episode_artifact_store import (
    EPISODE_SCRIPTS_CONFIG,
    NARRATIVE_PLAN_CONFIG,
    aggregate_episode_blob,
    persist_episode_blob_output,
)
from apps.drama.models import DramaEpisodeArtifact


class EpisodeArtifactStoreTests(TestCase):
    def setUp(self):
        AgentDefinitionService.ensure_defaults()
        self.user = get_user_model().objects.create_user(phone="13900006605", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="per-ep-scripts",
            theme="t",
            episode_count=60,
        )

    def test_persist_episode_scripts_writes_rows(self):
        persist_episode_blob_output(
            self.project,
            EPISODE_SCRIPTS_CONFIG,
            {
                "episodes": [
                    {"episodeNumber": 1, "full_script_text": "第一集正文"},
                    {"episodeNumber": 2, "full_script_text": "第二集正文"},
                ],
            },
            agent_id="drama.script-writer",
            run_id="run-1",
            episode_from=1,
            episode_to=2,
        )
        self.assertEqual(
            DramaEpisodeArtifact.objects.filter(
                project=self.project,
                artifact_key="episode_script",
            ).count(),
            2,
        )
        meta = get_artifact(self.project, "episode_scripts") or {}
        self.assertEqual(len(meta.get("episodes") or []), 2)

    def test_second_batch_scripts_merge(self):
        persist_episode_blob_output(
            self.project,
            EPISODE_SCRIPTS_CONFIG,
            {"episodes": [{"episodeNumber": n, "full_script_text": f"第{n}集"} for n in range(1, 11)]},
            agent_id="drama.script-writer",
            run_id="run-1",
            episode_from=1,
            episode_to=10,
        )
        persist_episode_blob_output(
            self.project,
            EPISODE_SCRIPTS_CONFIG,
            {
                "episodes": [
                    {"episodeNumber": 1, "full_script_text": "错标"},
                    {"episodeNumber": 2, "full_script_text": "错标2"},
                ],
            },
            agent_id="drama.script-writer",
            run_id="run-2",
            episode_from=11,
            episode_to=20,
        )
        aggregated = aggregate_episode_blob(self.project, EPISODE_SCRIPTS_CONFIG)
        nums = [ep["episodeNumber"] for ep in aggregated["episodes"]]
        self.assertEqual(nums, list(range(1, 13)))
        by_num = {ep["episodeNumber"]: ep["full_script_text"] for ep in aggregated["episodes"]}
        self.assertEqual(by_num[1], "第1集")
        self.assertEqual(by_num[11], "错标")

    def test_legacy_backfill_scripts(self):
        save_artifact(
            self.project,
            "episode_scripts",
            {
                "nodeId": "n1",
                "episodes": [{"episodeNumber": 3, "full_script_text": "legacy3"}],
            },
        )
        payload = get_artifact(self.project, "episode_scripts") or {}
        self.assertEqual(len(payload.get("episodes") or []), 1)
        self.assertTrue(
            DramaEpisodeArtifact.objects.filter(
                project=self.project,
                artifact_key="episode_script",
            ).exists()
        )

    def test_narrative_plan_per_episode(self):
        persist_episode_blob_output(
            self.project,
            NARRATIVE_PLAN_CONFIG,
            {
                "narrative_core_objective": "全剧叙事目标",
                "episode_narrative_designs": [
                    {"episode_id": "E001", "narrative_focus": "开篇钩子"},
                    {"episode_id": "E002", "narrative_focus": "关系升温"},
                ],
            },
            agent_id="drama.narrative-engineer",
            run_id="run-n1",
            episode_from=1,
            episode_to=2,
        )
        payload = get_artifact(self.project, "narrative_plan") or {}
        self.assertEqual(payload.get("narrative_core_objective"), "全剧叙事目标")
        self.assertEqual(len(payload.get("episode_narrative_designs") or []), 2)

    def test_summarize_episode_blob_progress(self):
        persist_episode_blob_output(
            self.project,
            EPISODE_SCRIPTS_CONFIG,
            {"episodes": [{"episodeNumber": n, "full_script_text": f"第{n}集"} for n in range(1, 6)]},
            agent_id="drama.script-writer",
            run_id="run-1",
            episode_from=1,
            episode_to=5,
        )
        from apps.drama.episode_artifact_store import summarize_episode_blob_progress

        summary = summarize_episode_blob_progress(self.project, EPISODE_SCRIPTS_CONFIG, batch_size=5)
        self.assertEqual(summary["generated"], 5)
        self.assertEqual(summary["suggested_range"], "6-10")

    def test_narrative_episodes_only_ignores_structure(self):
        persist_episode_blob_output(
            self.project,
            NARRATIVE_PLAN_CONFIG,
            {
                "narrative_core_objective": "全剧目标",
                "episode_narrative_designs": [
                    {"episode_id": "E001", "narrative_focus": "开篇"},
                ],
            },
            agent_id="drama.narrative-engineer",
            run_id="run-1",
            episode_from=1,
            episode_to=1,
        )
        persist_episode_blob_output(
            self.project,
            NARRATIVE_PLAN_CONFIG,
            {
                "narrative_core_objective": "应被忽略",
                "narrative_mechanics": [{"mechanism_type": "hook", "description": "新机制"}],
                "episode_narrative_designs": [{"episode_id": "E002", "narrative_focus": "第二集"}],
            },
            agent_id="drama.narrative-engineer",
            run_id="run-2",
            episode_from=2,
            episode_to=2,
            run_params={"blob_mode": "episodes_only"},
        )
        payload = get_artifact(self.project, "narrative_plan") or {}
        self.assertEqual(payload.get("narrative_core_objective"), "全剧目标")
        self.assertNotIn("narrative_mechanics", payload)
        self.assertEqual(len(payload.get("episode_narrative_designs") or []), 2)

    def test_narrative_structure_only_without_episodes(self):
        from apps.drama.artifact_mode import ARTIFACT_MODE_STRUCTURE_ONLY

        persist_episode_blob_output(
            self.project,
            NARRATIVE_PLAN_CONFIG,
            {
                "episode_narrative_designs": [{"episode_id": "E001", "narrative_focus": "已有"}],
            },
            agent_id="drama.narrative-engineer",
            run_id="run-ep",
            episode_from=1,
            episode_to=1,
        )
        persist_episode_blob_output(
            self.project,
            NARRATIVE_PLAN_CONFIG,
            {
                "narrative_core_objective": "补框架",
                "narrative_mechanics": [{"mechanism_type": "emotion", "description": "情绪曲线"}],
            },
            agent_id="drama.narrative-engineer",
            run_id="run-struct",
            run_params={"blob_mode": ARTIFACT_MODE_STRUCTURE_ONLY},
        )
        payload = get_artifact(self.project, "narrative_plan") or {}
        self.assertEqual(payload.get("narrative_core_objective"), "补框架")
        self.assertEqual(len(payload.get("episode_narrative_designs") or []), 1)

        from apps.drama.episode_artifact_store import summarize_episode_blob_progress

        summary = summarize_episode_blob_progress(self.project, NARRATIVE_PLAN_CONFIG, batch_size=5)
        self.assertTrue(summary["has_structure"])

    def test_independent_persist_routes_episode_scripts(self):
        agent = AgentDefinitionService.get_runnable("drama.script-writer")
        run = AgentExecutionRun.objects.create(
            project=self.project,
            user=self.user,
            agent_id="drama.script-writer",
            status=AgentExecutionRun.STATUS_RUNNING,
            batch_from=1,
            batch_to=1,
            run_params={"episode_range": "1-1"},
        )
        IndependentAgentService.persist_agent_output(
            self.project,
            agent,
            run,
            {
                "episode_scripts": {
                    "episodes": [{"episodeNumber": 1, "full_script_text": "剧本A"}],
                }
            },
            prompt_version="v1",
        )
        self.assertEqual(
            DramaEpisodeArtifact.objects.filter(
                project=self.project,
                artifact_key="episode_script",
            ).count(),
            1,
        )
