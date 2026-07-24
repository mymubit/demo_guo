# -*- coding: utf-8 -*-
"""V3 W2：选题 Topic REST API（eager + mock LLM）。"""
from __future__ import annotations

import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.models import V3ArtifactVersion, V3Project
from apps.drama.tests.helpers import SKILLS_ROOT

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
_BRIEF_PAYLOAD = json.loads(
    (_FIXTURE_DIR / "v3_project_brief_candidate.json").read_text(encoding="utf-8")
)


def _mock_llm_call(prompt: str) -> str:
    return json.dumps(_BRIEF_PAYLOAD, ensure_ascii=False)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    V3_LLM_CALL_OVERRIDE=_mock_llm_call,
)
class V3TopicApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="topic_api", password="pass12345"
        )
        self.other = user_model.objects.create_user(
            username="topic_other", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.project = V3Project.objects.create(
            owner=self.user,
            title="选题 API 项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.TOPIC,
        )
        self.base = f"/api/v3/projects/{self.project.id}/topic"

    def test_get_empty_topic_state(self) -> None:
        resp = self.client.get(f"{self.base}/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(data["stage"], "topic")
        self.assertIsNone(data["committed"])
        self.assertIsNone(data["candidate"])
        self.assertIsNone(data["draft"])
        self.assertIsNone(data["latest_run"])

    def test_generate_get_candidate_confirm_get_committed(self) -> None:
        gen = self.client.post(f"{self.base}/generate/")
        self.assertEqual(gen.status_code, 200)
        gen_body = gen.json()
        self.assertEqual(gen_body["code"], 0)
        run = gen_body["data"]["command_run"]
        self.assertEqual(run["command_type"], "generate_topic_brief")
        self.assertEqual(run["status"], "succeeded")

        after_gen = self.client.get(f"{self.base}/")
        self.assertEqual(after_gen.status_code, 200)
        state = after_gen.json()["data"]
        self.assertIsNotNone(state["candidate"])
        self.assertEqual(state["candidate"]["artifact_key"], "project_brief")
        self.assertEqual(state["candidate"]["status"], "candidate")
        self.assertEqual(state["candidate"]["payload"]["title"], _BRIEF_PAYLOAD["title"])
        self.assertIsNone(state["committed"])
        self.assertIsNotNone(state["latest_run"])
        self.assertEqual(state["latest_run"]["id"], run["id"])

        confirm = self.client.post(f"{self.base}/confirm/", {}, format="json")
        self.assertEqual(confirm.status_code, 200)
        confirm_run = confirm.json()["data"]["command_run"]
        self.assertEqual(confirm_run["command_type"], "confirm_topic_brief")
        self.assertEqual(confirm_run["status"], "succeeded")

        after_confirm = self.client.get(f"{self.base}/")
        self.assertEqual(after_confirm.status_code, 200)
        final = after_confirm.json()["data"]
        self.assertEqual(final["stage"], "blueprint")
        self.assertIsNotNone(final["committed"])
        self.assertEqual(final["committed"]["status"], "committed")
        self.assertEqual(final["committed"]["payload"]["title"], _BRIEF_PAYLOAD["title"])
        self.assertIsNone(final["candidate"])
        self.project.refresh_from_db()
        self.assertEqual(self.project.stage, V3Project.Stage.BLUEPRINT)

    def test_put_draft_and_confirm_use_draft(self) -> None:
        draft_payload = {**_BRIEF_PAYLOAD, "title": "人工编辑草稿标题"}
        put = self.client.put(
            f"{self.base}/draft/",
            {"payload": draft_payload},
            format="json",
        )
        self.assertEqual(put.status_code, 200)
        draft = put.json()["data"]
        self.assertEqual(draft["status"], "draft")
        self.assertEqual(draft["artifact_key"], "project_brief")
        self.assertEqual(draft["payload"]["title"], "人工编辑草稿标题")

        get_state = self.client.get(f"{self.base}/")
        self.assertEqual(get_state.json()["data"]["draft"]["payload"]["title"], "人工编辑草稿标题")

        # 无 candidate 时也可 use_draft 确认
        confirm = self.client.post(
            f"{self.base}/confirm/",
            {"use_draft": True},
            format="json",
        )
        self.assertEqual(confirm.status_code, 200)
        self.assertEqual(confirm.json()["data"]["command_run"]["status"], "succeeded")

        final = self.client.get(f"{self.base}/").json()["data"]
        self.assertEqual(final["stage"], "blueprint")
        self.assertEqual(final["committed"]["payload"]["title"], "人工编辑草稿标题")
        self.assertIsNone(final["draft"])

    def test_owner_isolation_returns_404(self) -> None:
        foreign = V3Project.objects.create(
            owner=self.other,
            title="他人选题",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        paths = [
            ("get", f"/api/v3/projects/{foreign.id}/topic/"),
            ("put", f"/api/v3/projects/{foreign.id}/topic/draft/"),
            ("post", f"/api/v3/projects/{foreign.id}/topic/generate/"),
            ("post", f"/api/v3/projects/{foreign.id}/topic/confirm/"),
        ]
        for method, path in paths:
            if method == "get":
                resp = self.client.get(path)
            elif method == "put":
                resp = self.client.put(path, {"payload": _BRIEF_PAYLOAD}, format="json")
            else:
                resp = self.client.post(path, {}, format="json")
            self.assertEqual(resp.status_code, 404, msg=path)

    def test_unauthenticated_rejected(self) -> None:
        self.client.force_authenticate(user=None)
        resp = self.client.get(f"{self.base}/")
        self.assertIn(resp.status_code, (401, 403))
