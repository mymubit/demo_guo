# -*- coding: utf-8 -*-
"""W3 Task 3：executor 分集/正文 JSON 形态（fake llm_call）。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3Project
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.skills_bridge.executor import (
    GenerationError,
    execute_generation,
    merge_episode_plan_revision,
)
from apps.drama.skills_bridge.validate import validate_artifact_payload
from apps.drama.tests.helpers import SKILLS_ROOT

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_BRIEF_PATH = _FIXTURES / "v3_project_brief_candidate.json"
_BLUEPRINT_PATH = _FIXTURES / "v3_blueprint_bundle.json"
_EPISODE_PLAN_PATH = _FIXTURES / "v3_episode_plan_candidate.json"
_EPISODE_SCRIPTS_PATH = _FIXTURES / "v3_episode_scripts_candidate.json"
_MEMORY_CHECKPOINT_PATH = _FIXTURES / "v3_memory_checkpoint_candidate.json"


def _clone_episode_card(card: dict, *, episode: int, title: str) -> dict:
    cloned = copy.deepcopy(card)
    cloned["episode"] = episode
    cloned["title"] = title
    return cloned


def _two_episode_plan(base: dict) -> dict:
    plan = copy.deepcopy(base)
    ep1 = plan["episodes"][0]
    plan["episodes"] = [
        ep1,
        _clone_episode_card(ep1, episode=2, title="证据初现"),
    ]
    return plan


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class MergeEpisodePlanRevisionTests(TestCase):
    """合并逻辑单测：范围外卡片不变。"""

    def test_merge_keeps_out_of_range_cards_unchanged(self) -> None:
        committed = _two_episode_plan(
            json.loads(_EPISODE_PLAN_PATH.read_text(encoding="utf-8"))
        )
        original_ep1 = copy.deepcopy(committed["episodes"][0])
        original_ep2_title = committed["episodes"][1]["title"]

        revised_ep2 = _clone_episode_card(
            committed["episodes"][1],
            episode=2,
            title="修订后的第二集标题",
        )
        llm_partial = {
            "schema_version": 2,
            "artifact_version": 1,
            "based_on": {"story_bible": 1},
            "episodes": [revised_ep2],
        }

        merged = merge_episode_plan_revision(
            committed_payload=committed,
            llm_payload=llm_partial,
            episode_numbers=[2],
        )

        self.assertEqual(len(merged["episodes"]), 2)
        self.assertEqual(merged["episodes"][0], original_ep1)
        self.assertEqual(merged["episodes"][1]["title"], "修订后的第二集标题")
        self.assertNotEqual(merged["episodes"][1]["title"], original_ep2_title)
        self.assertEqual(validate_artifact_payload("episode_plan", merged), [])


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class EpisodeExecutorTests(TestCase):
    def setUp(self) -> None:
        get_skills_loader.cache_clear()
        self.user = get_user_model().objects.create_user(
            username="ep_exec", password="pass12345"
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="分集执行器项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.EPISODES,
        )
        self.brief = json.loads(_BRIEF_PATH.read_text(encoding="utf-8"))
        self.blueprint = json.loads(_BLUEPRINT_PATH.read_text(encoding="utf-8"))
        self.episode_plan = json.loads(_EPISODE_PLAN_PATH.read_text(encoding="utf-8"))
        self.scripts = json.loads(_EPISODE_SCRIPTS_PATH.read_text(encoding="utf-8"))
        self.checkpoint = json.loads(_MEMORY_CHECKPOINT_PATH.read_text(encoding="utf-8"))

    def _commit(self, key: str, payload: dict, version: int = 1) -> V3ArtifactVersion:
        return V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key=key,
            version=version,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=payload,
        )

    def _seed_blueprint_deps(self) -> None:
        self._commit("project_brief", self.brief)
        self._commit("story_bible", self.blueprint["story_bible"])

    def test_generate_episode_plan_with_fake_llm(self) -> None:
        self._seed_blueprint_deps()
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_episode_plan",
            status=V3CommandRun.Status.RUNNING,
        )

        def fake_llm(_prompt: str) -> str:
            return json.dumps(self.episode_plan, ensure_ascii=False)

        created = execute_generation(
            command_type="generate_episode_plan",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        self.assertEqual(len(created), 1)
        art = created[0]
        self.assertEqual(art.artifact_key, "episode_plan")
        self.assertEqual(art.status, V3ArtifactVersion.Status.CANDIDATE)
        self.assertEqual(art.command_run_id, run.id)
        self.assertEqual(art.payload["episodes"][0]["title"], "重生归来")
        self.assertEqual(validate_artifact_payload("episode_plan", art.payload), [])

    def test_revise_episode_plan_merges_into_committed_copy(self) -> None:
        self._seed_blueprint_deps()
        committed_plan = _two_episode_plan(self.episode_plan)
        self._commit("episode_plan", committed_plan)
        original_ep1 = copy.deepcopy(committed_plan["episodes"][0])

        revised_ep2 = _clone_episode_card(
            committed_plan["episodes"][1],
            episode=2,
            title="局部修订标题",
        )
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="revise_episode_plan",
            status=V3CommandRun.Status.RUNNING,
            request_payload={"episode_numbers": [2]},
        )

        def fake_llm(_prompt: str) -> str:
            # 仅返回局部 episodes（非整剧）
            return json.dumps(
                {
                    "schema_version": 2,
                    "artifact_version": 1,
                    "based_on": {"story_bible": 1},
                    "episodes": [revised_ep2],
                },
                ensure_ascii=False,
            )

        created = execute_generation(
            command_type="revise_episode_plan",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        self.assertEqual(len(created), 1)
        art = created[0]
        self.assertEqual(art.artifact_key, "episode_plan")
        self.assertEqual(art.status, V3ArtifactVersion.Status.CANDIDATE)
        self.assertEqual(len(art.payload["episodes"]), 2)
        self.assertEqual(art.payload["episodes"][0], original_ep1)
        self.assertEqual(art.payload["episodes"][1]["title"], "局部修订标题")
        self.assertEqual(validate_artifact_payload("episode_plan", art.payload), [])

    def test_write_episode_batch_returns_scripts_and_checkpoint(self) -> None:
        self._seed_blueprint_deps()
        self._commit("episode_plan", self.episode_plan)
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="write_episode_batch",
            status=V3CommandRun.Status.RUNNING,
            request_payload={"episode_range": {"start": 1, "end": 1}},
        )

        def fake_llm(_prompt: str) -> str:
            return json.dumps(
                {
                    "episode_scripts": self.scripts,
                    "memory_checkpoint": self.checkpoint,
                },
                ensure_ascii=False,
            )

        created = execute_generation(
            command_type="write_episode_batch",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        keys = [item.artifact_key for item in created]
        self.assertEqual(keys, ["episode_scripts", "memory_checkpoint"])
        for item in created:
            self.assertEqual(item.status, V3ArtifactVersion.Status.CANDIDATE)
            self.assertEqual(item.command_run_id, run.id)
            self.assertEqual(validate_artifact_payload(item.artifact_key, item.payload), [])
        scripts_art = created[0]
        self.assertEqual(scripts_art.payload["episodes"][0]["episode_number"], 1)
        checkpoint_art = created[1]
        self.assertEqual(checkpoint_art.payload["episode"], 1)

    def test_revise_without_committed_plan_raises(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="revise_episode_plan",
            status=V3CommandRun.Status.RUNNING,
            request_payload={"episode_numbers": [1]},
        )
        with self.assertRaises(GenerationError) as ctx:
            execute_generation(
                command_type="revise_episode_plan",
                project=self.project,
                run=run,
                llm_call=lambda _p: json.dumps(self.episode_plan),
            )
        self.assertIn("分集计划", str(ctx.exception))
