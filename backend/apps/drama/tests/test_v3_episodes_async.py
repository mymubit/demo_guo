# -*- coding: utf-8 -*-
"""V3 W3 Task 4：分集/正文 live 编排 + confirm（Celery eager + mock LLM）。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3Project
from apps.drama.orchestrator import dispatch_command
from apps.drama.skills_bridge.recipe_map import recipe_for
from apps.drama.tests.helpers import SKILLS_ROOT

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
_BRIEF_PAYLOAD = json.loads(
    (_FIXTURE_DIR / "v3_project_brief_candidate.json").read_text(encoding="utf-8")
)
_BLUEPRINT_BUNDLE = json.loads(
    (_FIXTURE_DIR / "v3_blueprint_bundle.json").read_text(encoding="utf-8")
)
_EPISODE_PLAN = json.loads(
    (_FIXTURE_DIR / "v3_episode_plan_candidate.json").read_text(encoding="utf-8")
)
_SCRIPTS = json.loads(
    (_FIXTURE_DIR / "v3_episode_scripts_candidate.json").read_text(encoding="utf-8")
)
_CHECKPOINT = json.loads(
    (_FIXTURE_DIR / "v3_memory_checkpoint_candidate.json").read_text(encoding="utf-8")
)
_BLUEPRINT_KEYS = recipe_for("generate_blueprint")["writes"]
_SCRIPT_KEYS = recipe_for("write_episode_batch")["writes"]


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


def _two_episode_scripts() -> dict:
    scripts = copy.deepcopy(_SCRIPTS)
    ep1 = scripts["episodes"][0]
    ep2 = copy.deepcopy(ep1)
    ep2["episode_number"] = 2
    ep2["title"] = "证据初现"
    ep2["script"] = "2-1 DAY INT. 档案馆\n林夏核对旧授权记录。"
    ep2["memory_checkpoint"] = copy.deepcopy(_CHECKPOINT)
    ep2["memory_checkpoint"]["episode"] = 2
    scripts["episodes"] = [ep1, ep2]
    return scripts


def _batch_checkpoint() -> dict:
    checkpoint = copy.deepcopy(_CHECKPOINT)
    checkpoint["episode"] = 2
    return checkpoint


def _mock_llm_call(prompt: str) -> str:
    if '"command_type": "write_episode_batch"' in prompt:
        return json.dumps(
            {
                "episode_scripts": _two_episode_scripts(),
                "memory_checkpoint": _batch_checkpoint(),
            },
            ensure_ascii=False,
        )
    if '"command_type": "revise_episode_plan"' in prompt:
        revised = _clone_episode_card(
            _EPISODE_PLAN["episodes"][0],
            episode=2,
            title="局部修订后的第二集",
        )
        return json.dumps(
            {
                "schema_version": 2,
                "artifact_version": 1,
                "based_on": {"story_bible": 1},
                "episodes": [revised],
            },
            ensure_ascii=False,
        )
    if '"command_type": "generate_episode_plan"' in prompt:
        return json.dumps(_two_episode_plan(_EPISODE_PLAN), ensure_ascii=False)
    if '"command_type": "generate_blueprint"' in prompt:
        return json.dumps(_BLUEPRINT_BUNDLE, ensure_ascii=False)
    return json.dumps(_BRIEF_PAYLOAD, ensure_ascii=False)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    V3_LLM_CALL_OVERRIDE=_mock_llm_call,
)
class V3EpisodesAsyncTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="ep_async_w3", password="pass12345"
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="分集编排项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.TOPIC,
        )

    def _commit(self, key: str, payload: dict, version: int = 1) -> V3ArtifactVersion:
        return V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key=key,
            version=version,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=payload,
        )

    def _seed_committed_blueprint(self) -> None:
        self._commit("project_brief", _BRIEF_PAYLOAD)
        for key in _BLUEPRINT_KEYS:
            self._commit(key, _BLUEPRINT_BUNDLE[key])
        self.project.stage = V3Project.Stage.EPISODES
        self.project.save(update_fields=["stage", "updated_at"])

    def test_generate_episode_plan_without_blueprint_fails_friendly(self) -> None:
        """1. 无蓝图生成分集 → failed 人话。"""
        self.project.stage = V3Project.Stage.EPISODES
        self.project.save(update_fields=["stage", "updated_at"])

        run = dispatch_command(
            owner=self.user,
            command_type="generate_episode_plan",
            payload={"project_id": str(self.project.id)},
        )
        run.refresh_from_db()
        self.assertEqual(run.status, V3CommandRun.Status.FAILED)
        self.assertTrue(run.error_message)
        self.assertNotIn("Traceback", run.error_message)
        self.assertFalse(
            V3ArtifactVersion.objects.filter(
                project=self.project, artifact_key="episode_plan"
            ).exists()
        )

    def test_generate_and_confirm_episode_plan_advances_to_writing(self) -> None:
        """2. 有蓝图 → generate plan → confirm → stage writing。"""
        self._seed_committed_blueprint()

        gen = dispatch_command(
            owner=self.user,
            command_type="generate_episode_plan",
            payload={"project_id": str(self.project.id)},
        )
        gen.refresh_from_db()
        self.assertEqual(gen.status, V3CommandRun.Status.SUCCEEDED)
        artifact_ids = gen.result_payload.get("artifact_ids") or []
        self.assertEqual(len(artifact_ids), 1)
        art = V3ArtifactVersion.objects.get(id=artifact_ids[0])
        self.assertEqual(art.artifact_key, "episode_plan")
        self.assertEqual(art.status, V3ArtifactVersion.Status.CANDIDATE)

        confirm = dispatch_command(
            owner=self.user,
            command_type="confirm_episode_plan",
            payload={"project_id": str(self.project.id)},
        )
        self.assertEqual(confirm.status, V3CommandRun.Status.SUCCEEDED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.stage, V3Project.Stage.WRITING)
        committed = V3ArtifactVersion.objects.get(
            project=self.project,
            artifact_key="episode_plan",
            status=V3ArtifactVersion.Status.COMMITTED,
        )
        self.assertEqual(len(committed.payload["episodes"]), 2)

    def test_revise_episode_plan_only_changes_selected_episode(self) -> None:
        """3. revise 仅改 ep 2 → 其它集不变。"""
        self._seed_committed_blueprint()
        committed_plan = _two_episode_plan(_EPISODE_PLAN)
        self._commit("episode_plan", committed_plan)
        original_ep1 = copy.deepcopy(committed_plan["episodes"][0])

        run = dispatch_command(
            owner=self.user,
            command_type="revise_episode_plan",
            payload={
                "project_id": str(self.project.id),
                "episode_numbers": [2],
            },
        )
        run.refresh_from_db()
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        art = V3ArtifactVersion.objects.get(
            id=(run.result_payload.get("artifact_ids") or [])[0]
        )
        self.assertEqual(art.status, V3ArtifactVersion.Status.CANDIDATE)
        self.assertEqual(len(art.payload["episodes"]), 2)
        self.assertEqual(art.payload["episodes"][0], original_ep1)
        self.assertEqual(art.payload["episodes"][1]["title"], "局部修订后的第二集")
        self.assertEqual(art.payload["episodes"][1]["episode"], 2)

    def test_write_episode_batch_1_to_2_writes_two_candidates(self) -> None:
        """4. write 1–2 → episode_scripts + memory_checkpoint 两产物 candidate。"""
        self._seed_committed_blueprint()
        self._commit("episode_plan", _two_episode_plan(_EPISODE_PLAN))
        self.project.stage = V3Project.Stage.WRITING
        self.project.save(update_fields=["stage", "updated_at"])

        run = dispatch_command(
            owner=self.user,
            command_type="write_episode_batch",
            payload={
                "project_id": str(self.project.id),
                "episode_range": {"start": 1, "end": 2},
            },
        )
        run.refresh_from_db()
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        artifact_ids = run.result_payload.get("artifact_ids") or []
        self.assertEqual(len(artifact_ids), 2)
        arts = list(
            V3ArtifactVersion.objects.filter(id__in=artifact_ids).order_by("artifact_key")
        )
        self.assertEqual({a.artifact_key for a in arts}, set(_SCRIPT_KEYS))
        self.assertTrue(
            all(a.status == V3ArtifactVersion.Status.CANDIDATE for a in arts)
        )
        scripts = next(a for a in arts if a.artifact_key == "episode_scripts")
        self.assertEqual(
            [ep["episode_number"] for ep in scripts.payload["episodes"]],
            [1, 2],
        )

    def test_confirm_script_candidate_commits_scripts_and_checkpoint(self) -> None:
        """5. confirm scripts → episode_scripts / memory_checkpoint committed。"""
        self._seed_committed_blueprint()
        self._commit("episode_plan", _two_episode_plan(_EPISODE_PLAN))
        self.project.stage = V3Project.Stage.WRITING
        self.project.save(update_fields=["stage", "updated_at"])

        gen = dispatch_command(
            owner=self.user,
            command_type="write_episode_batch",
            payload={
                "project_id": str(self.project.id),
                "episode_range": {"start": 1, "end": 2},
            },
        )
        self.assertEqual(gen.status, V3CommandRun.Status.SUCCEEDED)

        confirm = dispatch_command(
            owner=self.user,
            command_type="confirm_script_candidate",
            payload={"project_id": str(self.project.id)},
        )
        self.assertEqual(confirm.status, V3CommandRun.Status.SUCCEEDED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.stage, V3Project.Stage.WRITING)
        for key in _SCRIPT_KEYS:
            self.assertTrue(
                V3ArtifactVersion.objects.filter(
                    project=self.project,
                    artifact_key=key,
                    status=V3ArtifactVersion.Status.COMMITTED,
                ).exists(),
                msg=f"missing committed {key}",
            )
        self.assertEqual(
            V3ArtifactVersion.objects.filter(
                project=self.project,
                artifact_key__in=_SCRIPT_KEYS,
                status=V3ArtifactVersion.Status.CANDIDATE,
            ).count(),
            0,
        )

    def test_double_generate_episode_plan_confirm_leaves_no_residual_candidates(
        self,
    ) -> None:
        """6. 双 generate plan → confirm 后无残留 candidate（回归 supersede）。"""
        self._seed_committed_blueprint()

        first = dispatch_command(
            owner=self.user,
            command_type="generate_episode_plan",
            payload={"project_id": str(self.project.id)},
        )
        self.assertEqual(first.status, V3CommandRun.Status.SUCCEEDED)
        old_id = (first.result_payload.get("artifact_ids") or [])[0]

        second = dispatch_command(
            owner=self.user,
            command_type="generate_episode_plan",
            payload={"project_id": str(self.project.id)},
        )
        self.assertEqual(second.status, V3CommandRun.Status.SUCCEEDED)
        latest_id = (second.result_payload.get("artifact_ids") or [])[0]
        self.assertNotEqual(old_id, latest_id)

        old_art = V3ArtifactVersion.objects.get(id=old_id)
        self.assertEqual(old_art.status, V3ArtifactVersion.Status.SUPERSEDED)
        self.assertEqual(
            V3ArtifactVersion.objects.filter(
                project=self.project,
                artifact_key="episode_plan",
                status=V3ArtifactVersion.Status.CANDIDATE,
            ).count(),
            1,
        )

        confirm = dispatch_command(
            owner=self.user,
            command_type="confirm_episode_plan",
            payload={
                "project_id": str(self.project.id),
                "artifact_version_ids": [latest_id],
            },
        )
        self.assertEqual(confirm.status, V3CommandRun.Status.SUCCEEDED)
        self.assertEqual(
            V3ArtifactVersion.objects.filter(
                project=self.project,
                artifact_key="episode_plan",
                status=V3ArtifactVersion.Status.CANDIDATE,
            ).count(),
            0,
        )
        committed = V3ArtifactVersion.objects.get(id=latest_id)
        self.assertEqual(committed.status, V3ArtifactVersion.Status.COMMITTED)
        old_art.refresh_from_db()
        self.assertEqual(old_art.status, V3ArtifactVersion.Status.SUPERSEDED)
