# -*- coding: utf-8 -*-
"""V3 W2：蓝图 Blueprint REST API（eager + mock LLM）。"""
from __future__ import annotations

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
_BLUEPRINT_KEYS = recipe_for("generate_blueprint")["writes"]


def _mock_llm_call(prompt: str) -> str:
    if '"command_type": "generate_blueprint"' in prompt:
        return json.dumps(_BLUEPRINT_BUNDLE, ensure_ascii=False)
    return json.dumps(_BRIEF_PAYLOAD, ensure_ascii=False)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    V3_LLM_CALL_OVERRIDE=_mock_llm_call,
)
class V3BlueprintApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="bp_api", password="pass12345"
        )
        self.other = user_model.objects.create_user(
            username="bp_other", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.project = V3Project.objects.create(
            owner=self.user,
            title="蓝图 API 项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.BLUEPRINT,
        )
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=1,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=_BRIEF_PAYLOAD,
        )
        self.base = f"/api/v3/projects/{self.project.id}/blueprint"

    def test_get_empty_blueprint_state(self) -> None:
        resp = self.client.get(f"{self.base}/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertIsNone(data["committed"])
        self.assertIsNone(data["candidate"])
        self.assertIsNone(data["latest_run"])

    def test_generate_get_candidates_confirm_get_committed(self) -> None:
        gen = self.client.post(f"{self.base}/generate/")
        self.assertEqual(gen.status_code, 200)
        gen_body = gen.json()
        self.assertEqual(gen_body["code"], 0)
        run = gen_body["data"]["command_run"]
        self.assertEqual(run["command_type"], "generate_blueprint")
        self.assertEqual(run["status"], "succeeded")

        after_gen = self.client.get(f"{self.base}/")
        self.assertEqual(after_gen.status_code, 200)
        state = after_gen.json()["data"]
        self.assertIsNotNone(state["candidate"])
        for key in _BLUEPRINT_KEYS:
            self.assertIn(key, state["candidate"])
            item = state["candidate"][key]
            self.assertEqual(item["artifact_key"], key)
            self.assertEqual(item["status"], "candidate")
        self.assertIsNone(state["committed"])
        self.assertEqual(state["latest_run"]["id"], run["id"])

        confirm = self.client.post(f"{self.base}/confirm/", {}, format="json")
        self.assertEqual(confirm.status_code, 200)
        confirm_run = confirm.json()["data"]["command_run"]
        self.assertEqual(confirm_run["command_type"], "confirm_blueprint")
        self.assertEqual(confirm_run["status"], "succeeded")

        after_confirm = self.client.get(f"{self.base}/")
        self.assertEqual(after_confirm.status_code, 200)
        final = after_confirm.json()["data"]
        self.assertIsNotNone(final["committed"])
        for key in _BLUEPRINT_KEYS:
            self.assertEqual(final["committed"][key]["status"], "committed")
        self.assertIsNone(final["candidate"])
        self.project.refresh_from_db()
        self.assertEqual(self.project.stage, V3Project.Stage.EPISODES)

    def test_generate_without_brief_fails_friendly(self) -> None:
        bare = V3Project.objects.create(
            owner=self.user,
            title="无简报",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.TOPIC,
        )
        resp = self.client.post(f"/api/v3/projects/{bare.id}/blueprint/generate/")
        self.assertEqual(resp.status_code, 200)
        run = resp.json()["data"]["command_run"]
        self.assertEqual(run["status"], "failed")
        self.assertIn("简报", run["error_message"])

    def test_owner_isolation_returns_404(self) -> None:
        foreign = V3Project.objects.create(
            owner=self.other,
            title="他人蓝图",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        for method, path in [
            ("get", f"/api/v3/projects/{foreign.id}/blueprint/"),
            ("post", f"/api/v3/projects/{foreign.id}/blueprint/generate/"),
            ("post", f"/api/v3/projects/{foreign.id}/blueprint/confirm/"),
        ]:
            resp = (
                self.client.get(path)
                if method == "get"
                else self.client.post(path, {}, format="json")
            )
            self.assertEqual(resp.status_code, 404, msg=path)

    def test_generate_succeeds_when_llm_omits_story_bible_required_keys(self) -> None:
        """模拟线上漏字段：归一化后仍应 succeeded，不要求用户反复重试。"""
        import copy

        incomplete = copy.deepcopy(_BLUEPRINT_BUNDLE)
        for key in (
            "world_rules",
            "adapt_source",
            "relationship_map",
            "series_structure",
        ):
            incomplete["story_bible"].pop(key, None)
        # 对齐线上：角色缺 ghost
        char = dict(incomplete["story_bible"]["characters"][0])
        for key in ("ghost", "lie", "flaw"):
            char.pop(key, None)
        incomplete["story_bible"]["characters"] = [char]

        def _incomplete_llm(prompt: str) -> str:
            if '"command_type": "generate_blueprint"' in prompt:
                return json.dumps(incomplete, ensure_ascii=False)
            return json.dumps(_BRIEF_PAYLOAD, ensure_ascii=False)

        with override_settings(V3_LLM_CALL_OVERRIDE=_incomplete_llm):
            gen = self.client.post(f"{self.base}/generate/")
        self.assertEqual(gen.status_code, 200, gen.content)
        run = gen.json()["data"]["command_run"]
        self.assertEqual(run["status"], "succeeded", run.get("error_message"))
        bible = V3ArtifactVersion.objects.get(
            project=self.project,
            artifact_key="story_bible",
            status=V3ArtifactVersion.Status.CANDIDATE,
        )
        self.assertIn("world_rules", bible.payload)
        self.assertIn("series_structure", bible.payload)
        self.assertEqual(bible.payload["characters"][0].get("ghost"), "待细化")
