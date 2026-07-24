# -*- coding: utf-8 -*-
"""V3 W3：Scripts REST API + 草稿（eager + mock LLM）。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.models import V3ArtifactVersion, V3Project, V3ScriptDraft
from apps.drama.skills_bridge.recipe_map import recipe_for
from apps.drama.skills_bridge.validate import validate_artifact_payload
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
    if '"command_type": "generate_episode_plan"' in prompt:
        return json.dumps(_two_episode_plan(_EPISODE_PLAN), ensure_ascii=False)
    if '"command_type": "generate_blueprint"' in prompt:
        return json.dumps(_BLUEPRINT_BUNDLE, ensure_ascii=False)
    return json.dumps(_BRIEF_PAYLOAD, ensure_ascii=False)


_DRAFT_PAYLOAD = {
    "scenes": [
        {
            "id": "s1",
            "heading": "INT. 咖啡厅 - 日",
            "beats": [
                {"type": "action", "text": "主角推门而入。"},
                {"type": "dialogue", "text": "好久不见。", "character": "小明"},
            ],
        }
    ]
}


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    V3_LLM_CALL_OVERRIDE=_mock_llm_call,
)
class V3ScriptsApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="scripts_api", password="pass12345"
        )
        self.other = user_model.objects.create_user(
            username="scripts_other", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.project = V3Project.objects.create(
            owner=self.user,
            title="正文 API 项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.WRITING,
        )
        self._seed_committed_deps()
        self.base = f"/api/v3/projects/{self.project.id}/scripts"

    def _commit(self, key: str, payload: dict, version: int = 1) -> V3ArtifactVersion:
        return V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key=key,
            version=version,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=payload,
        )

    def _seed_committed_deps(self) -> None:
        self._commit("project_brief", _BRIEF_PAYLOAD)
        for key in _BLUEPRINT_KEYS:
            self._commit(key, _BLUEPRINT_BUNDLE[key])
        self._commit("episode_plan", _two_episode_plan(_EPISODE_PLAN))

    def test_get_empty_scripts_state(self) -> None:
        resp = self.client.get(f"{self.base}/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertIsNone(data["committed"])
        self.assertIsNone(data["candidate"])
        self.assertEqual(data["drafts"], [])
        self.assertIsNone(data["latest_run"])

    def test_put_draft_and_list_includes_draft(self) -> None:
        put = self.client.put(
            f"{self.base}/1/draft/",
            {"payload": _DRAFT_PAYLOAD},
            format="json",
        )
        self.assertEqual(put.status_code, 200)
        put_body = put.json()
        self.assertEqual(put_body["code"], 0)
        self.assertEqual(put_body["data"]["episode_number"], 1)
        self.assertEqual(put_body["data"]["payload"]["scenes"][0]["id"], "s1")
        self.assertIn("updated_at", put_body["data"])

        state = self.client.get(f"{self.base}/").json()["data"]
        self.assertEqual(len(state["drafts"]), 1)
        self.assertEqual(state["drafts"][0]["episode_number"], 1)
        self.assertEqual(state["drafts"][0]["payload"]["scenes"][0]["heading"], "INT. 咖啡厅 - 日")

        # 覆盖更新
        put2 = self.client.put(
            f"{self.base}/1/draft/",
            {"payload": {"scenes": [{"id": "s2", "heading": "新场", "beats": []}]}},
            format="json",
        )
        self.assertEqual(put2.status_code, 200)
        self.assertEqual(put2.json()["data"]["payload"]["scenes"][0]["id"], "s2")
        self.assertEqual(V3ScriptDraft.objects.filter(project=self.project).count(), 1)

    def test_get_episode_detail_slices(self) -> None:
        scripts = _two_episode_scripts()
        self._commit("episode_scripts", scripts)
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="episode_scripts",
            version=2,
            status=V3ArtifactVersion.Status.CANDIDATE,
            payload=scripts,
        )
        V3ScriptDraft.objects.create(
            project=self.project,
            episode_number=2,
            payload=_DRAFT_PAYLOAD,
        )

        resp = self.client.get(f"{self.base}/2/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["episode_number"], 2)
        self.assertEqual(data["committed"]["episode_number"], 2)
        self.assertEqual(data["committed"]["title"], "证据初现")
        self.assertEqual(data["candidate"]["episode_number"], 2)
        self.assertEqual(data["draft"]["episode_number"], 2)
        self.assertEqual(data["draft"]["payload"]["scenes"][0]["id"], "s1")

        missing = self.client.get(f"{self.base}/9/")
        self.assertEqual(missing.status_code, 200)
        empty = missing.json()["data"]
        self.assertEqual(empty["episode_number"], 9)
        self.assertIsNone(empty["committed"])
        self.assertIsNone(empty["candidate"])
        self.assertIsNone(empty["draft"])

    def test_generate_confirm_candidate_flow(self) -> None:
        gen = self.client.post(
            f"{self.base}/generate/",
            {"start": 1, "end": 2, "writing_requests": {"tone": "紧凑"}},
            format="json",
        )
        self.assertEqual(gen.status_code, 200)
        run = gen.json()["data"]["command_run"]
        self.assertEqual(run["command_type"], "write_episode_batch")
        self.assertEqual(run["status"], "succeeded")

        after_gen = self.client.get(f"{self.base}/").json()["data"]
        self.assertIsNotNone(after_gen["candidate"])
        self.assertEqual(after_gen["candidate"]["artifact_key"], "episode_scripts")
        self.assertEqual(len(after_gen["candidate"]["payload"]["episodes"]), 2)
        self.assertIsNone(after_gen["committed"])
        self.assertEqual(after_gen["latest_run"]["id"], run["id"])

        confirm = self.client.post(f"{self.base}/confirm/", {}, format="json")
        self.assertEqual(confirm.status_code, 200)
        confirm_run = confirm.json()["data"]["command_run"]
        self.assertEqual(confirm_run["command_type"], "confirm_script_candidate")
        self.assertEqual(confirm_run["status"], "succeeded")

        final = self.client.get(f"{self.base}/").json()["data"]
        self.assertIsNotNone(final["committed"])
        self.assertEqual(final["committed"]["status"], "committed")
        self.assertIsNone(final["candidate"])

    def test_confirm_use_drafts_validates_and_commits(self) -> None:
        base_scripts = _two_episode_scripts()
        self._commit("episode_scripts", base_scripts)
        old_checkpoint = self._commit("memory_checkpoint", _batch_checkpoint())
        V3ScriptDraft.objects.create(
            project=self.project,
            episode_number=1,
            payload=_DRAFT_PAYLOAD,
        )

        confirm = self.client.post(
            f"{self.base}/confirm/",
            {"use_drafts": True},
            format="json",
        )
        self.assertEqual(confirm.status_code, 200)
        run = confirm.json()["data"]["command_run"]
        self.assertEqual(run["command_type"], "confirm_script_candidate")
        self.assertEqual(run["status"], "succeeded")
        artifact_ids = run["result_payload"]["artifact_ids"]
        self.assertEqual(len(artifact_ids), 2)

        committed = V3ArtifactVersion.objects.filter(
            project=self.project,
            artifact_key="episode_scripts",
            status=V3ArtifactVersion.Status.COMMITTED,
        ).order_by("-version").first()
        self.assertIsNotNone(committed)
        self.assertEqual(validate_artifact_payload("episode_scripts", committed.payload), [])
        ep1 = next(
            ep for ep in committed.payload["episodes"] if ep["episode_number"] == 1
        )
        self.assertIn("INT. 咖啡厅 - 日", ep1["script"])
        self.assertIn("好久不见", ep1["script"])
        # 未改草稿的第 2 集保持原样
        ep2 = next(
            ep for ep in committed.payload["episodes"] if ep["episode_number"] == 2
        )
        self.assertEqual(ep2["script"], base_scripts["episodes"][1]["script"])

        old_checkpoint.refresh_from_db()
        self.assertEqual(old_checkpoint.status, V3ArtifactVersion.Status.SUPERSEDED)

        new_checkpoint = V3ArtifactVersion.objects.filter(
            project=self.project,
            artifact_key="memory_checkpoint",
            status=V3ArtifactVersion.Status.COMMITTED,
        ).order_by("-version").first()
        self.assertIsNotNone(new_checkpoint)
        self.assertNotEqual(str(new_checkpoint.id), str(old_checkpoint.id))
        self.assertEqual(new_checkpoint.payload["episode"], 2)
        self.assertIn(
            "人工已修订正文，续写须对齐最新脚本",
            new_checkpoint.payload["next_episode_constraints"],
        )
        self.assertEqual(
            validate_artifact_payload("memory_checkpoint", new_checkpoint.payload),
            [],
        )
        self.assertEqual(
            {str(committed.id), str(new_checkpoint.id)},
            set(artifact_ids),
        )

    def test_confirm_use_drafts_without_drafts_fails(self) -> None:
        self._commit("episode_scripts", _two_episode_scripts())
        confirm = self.client.post(
            f"{self.base}/confirm/",
            {"use_drafts": True},
            format="json",
        )
        self.assertEqual(confirm.status_code, 200)
        run = confirm.json()["data"]["command_run"]
        self.assertEqual(run["status"], "failed")
        self.assertTrue(run["error_message"])
        self.assertNotIn("Traceback", run["error_message"])

    def test_generate_requires_start_end(self) -> None:
        resp = self.client.post(f"{self.base}/generate/", {}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_put_draft_requires_payload(self) -> None:
        resp = self.client.put(f"{self.base}/1/draft/", {}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_owner_isolation_returns_404(self) -> None:
        foreign = V3Project.objects.create(
            owner=self.other,
            title="他人正文",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        paths = [
            ("get", f"/api/v3/projects/{foreign.id}/scripts/"),
            ("get", f"/api/v3/projects/{foreign.id}/scripts/1/"),
            ("put", f"/api/v3/projects/{foreign.id}/scripts/1/draft/"),
            ("post", f"/api/v3/projects/{foreign.id}/scripts/generate/"),
            ("post", f"/api/v3/projects/{foreign.id}/scripts/confirm/"),
        ]
        for method, path in paths:
            if method == "get":
                resp = self.client.get(path)
            elif method == "put":
                resp = self.client.put(
                    path, {"payload": _DRAFT_PAYLOAD}, format="json"
                )
            elif "generate" in path:
                resp = self.client.post(
                    path, {"start": 1, "end": 1}, format="json"
                )
            else:
                resp = self.client.post(path, {}, format="json")
            self.assertEqual(resp.status_code, 404, msg=path)
