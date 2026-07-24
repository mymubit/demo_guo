# -*- coding: utf-8 -*-
"""V3 W3：分集 Episodes REST API（eager + mock LLM）。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.models import V3ArtifactVersion, V3Project
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
_BLUEPRINT_KEYS = recipe_for("generate_blueprint")["writes"]


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


def _mock_llm_call(prompt: str) -> str:
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
class V3EpisodesApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="ep_api", password="pass12345"
        )
        self.other = user_model.objects.create_user(
            username="ep_other", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.project = V3Project.objects.create(
            owner=self.user,
            title="分集 API 项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.EPISODES,
        )
        self._seed_committed_blueprint()
        self.base = f"/api/v3/projects/{self.project.id}/episodes"

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

    def test_get_empty_episodes_state(self) -> None:
        resp = self.client.get(f"{self.base}/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(data["stage"], "episodes")
        self.assertIsNone(data["committed"])
        self.assertIsNone(data["candidate"])
        self.assertIsNone(data["latest_run"])

    def test_generate_get_candidate_confirm_get_committed(self) -> None:
        gen = self.client.post(
            f"{self.base}/generate/",
            {
                "episode_count": 2,
                "duration_target": "90s",
                "planning_requests": {"tone": "紧凑"},
            },
            format="json",
        )
        self.assertEqual(gen.status_code, 200)
        gen_body = gen.json()
        self.assertEqual(gen_body["code"], 0)
        run = gen_body["data"]["command_run"]
        self.assertEqual(run["command_type"], "generate_episode_plan")
        self.assertEqual(run["status"], "succeeded")

        after_gen = self.client.get(f"{self.base}/")
        self.assertEqual(after_gen.status_code, 200)
        state = after_gen.json()["data"]
        self.assertEqual(state["stage"], "episodes")
        self.assertIsNotNone(state["candidate"])
        self.assertEqual(state["candidate"]["artifact_key"], "episode_plan")
        self.assertEqual(state["candidate"]["status"], "candidate")
        self.assertEqual(len(state["candidate"]["payload"]["episodes"]), 2)
        self.assertIsNone(state["committed"])
        self.assertEqual(state["latest_run"]["id"], run["id"])

        confirm = self.client.post(f"{self.base}/confirm/", {}, format="json")
        self.assertEqual(confirm.status_code, 200)
        confirm_run = confirm.json()["data"]["command_run"]
        self.assertEqual(confirm_run["command_type"], "confirm_episode_plan")
        self.assertEqual(confirm_run["status"], "succeeded")

        after_confirm = self.client.get(f"{self.base}/")
        self.assertEqual(after_confirm.status_code, 200)
        final = after_confirm.json()["data"]
        self.assertEqual(final["stage"], "writing")
        self.assertIsNotNone(final["committed"])
        self.assertEqual(final["committed"]["status"], "committed")
        self.assertIsNone(final["candidate"])
        self.project.refresh_from_db()
        self.assertEqual(self.project.stage, V3Project.Stage.WRITING)

    def test_revise_selected_episodes(self) -> None:
        committed_plan = _two_episode_plan(_EPISODE_PLAN)
        self._commit("episode_plan", committed_plan)
        original_ep1 = copy.deepcopy(committed_plan["episodes"][0])

        revise = self.client.post(
            f"{self.base}/revise/",
            {
                "episode_numbers": [2],
                "revision_requests": {"hook": "加强悬念"},
            },
            format="json",
        )
        self.assertEqual(revise.status_code, 200)
        run = revise.json()["data"]["command_run"]
        self.assertEqual(run["command_type"], "revise_episode_plan")
        self.assertEqual(run["status"], "succeeded")

        state = self.client.get(f"{self.base}/").json()["data"]
        self.assertIsNotNone(state["candidate"])
        episodes = state["candidate"]["payload"]["episodes"]
        self.assertEqual(len(episodes), 2)
        self.assertEqual(episodes[0], original_ep1)
        self.assertEqual(episodes[1]["title"], "局部修订后的第二集")

    def test_revise_requires_episode_numbers(self) -> None:
        resp = self.client.post(f"{self.base}/revise/", {}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_generate_without_blueprint_fails_friendly(self) -> None:
        bare = V3Project.objects.create(
            owner=self.user,
            title="无蓝图",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.EPISODES,
        )
        resp = self.client.post(f"/api/v3/projects/{bare.id}/episodes/generate/")
        self.assertEqual(resp.status_code, 200)
        run = resp.json()["data"]["command_run"]
        self.assertEqual(run["status"], "failed")
        self.assertTrue(run["error_message"])
        self.assertNotIn("Traceback", run["error_message"])

    def test_owner_isolation_returns_404(self) -> None:
        foreign = V3Project.objects.create(
            owner=self.other,
            title="他人分集",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        for method, path in [
            ("get", f"/api/v3/projects/{foreign.id}/episodes/"),
            ("post", f"/api/v3/projects/{foreign.id}/episodes/generate/"),
            ("post", f"/api/v3/projects/{foreign.id}/episodes/confirm/"),
            ("post", f"/api/v3/projects/{foreign.id}/episodes/revise/"),
        ]:
            if method == "get":
                resp = self.client.get(path)
            elif "revise" in path:
                resp = self.client.post(
                    path, {"episode_numbers": [1]}, format="json"
                )
            else:
                resp = self.client.post(path, {}, format="json")
            self.assertEqual(resp.status_code, 404, msg=path)
