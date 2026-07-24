# -*- coding: utf-8 -*-
"""V3 P3-W3：产物版本列表与回滚。"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.models import V3ArtifactVersion, V3Project
from apps.drama.orchestrator.artifact_rollback import (
    ALLOWED_ROLLBACK_KEYS,
    ArtifactRollbackError,
    list_committed_versions,
    rollback_artifact,
)
from apps.drama.tests.helpers import SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=str(SKILLS_ROOT))
class ArtifactRollbackServiceTests(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="rollback_svc", password="pass12345"
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="回滚服务测试",
            entry_type=V3Project.EntryType.ORIGINAL,
        )

    def _seed_brief_history(self) -> None:
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=1,
            status=V3ArtifactVersion.Status.SUPERSEDED,
            payload={"title": "v1 选题"},
        )
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=2,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload={"title": "v2 选题"},
        )
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=3,
            status=V3ArtifactVersion.Status.CANDIDATE,
            payload={"title": "候选勿回滚"},
        )

    def test_allowed_keys_cover_r2(self) -> None:
        expected = {
            "project_brief",
            "story_bible",
            "character_system",
            "world_system",
            "emotion_system",
            "originality_report",
            "episode_plan",
            "episode_scripts",
        }
        self.assertEqual(set(ALLOWED_ROLLBACK_KEYS), expected)

    def test_list_committed_excludes_candidate(self) -> None:
        self._seed_brief_history()
        items = list_committed_versions(self.project, "project_brief")
        self.assertEqual([a.version for a in items], [2, 1])
        self.assertTrue(all(a.status != "candidate" for a in items))

    def test_list_rejects_unknown_key(self) -> None:
        with self.assertRaises(ArtifactRollbackError):
            list_committed_versions(self.project, "memory_checkpoint")

    def test_rollback_copies_payload_to_new_committed(self) -> None:
        self._seed_brief_history()
        created = rollback_artifact(
            project=self.project,
            artifact_key="project_brief",
            source_version=1,
            actor=self.user.username,
        )
        self.assertEqual(created.version, 4)
        self.assertEqual(created.status, V3ArtifactVersion.Status.COMMITTED)
        self.assertEqual(created.payload["title"], "v1 选题")

        v2 = V3ArtifactVersion.objects.get(
            project=self.project, artifact_key="project_brief", version=2
        )
        self.assertEqual(v2.status, V3ArtifactVersion.Status.SUPERSEDED)
        cand = V3ArtifactVersion.objects.get(
            project=self.project, artifact_key="project_brief", version=3
        )
        self.assertEqual(cand.status, V3ArtifactVersion.Status.SUPERSEDED)

        committed = V3ArtifactVersion.objects.filter(
            project=self.project,
            artifact_key="project_brief",
            status=V3ArtifactVersion.Status.COMMITTED,
        )
        self.assertEqual(committed.count(), 1)
        self.assertEqual(committed.get().id, created.id)

    def test_rollback_rejects_candidate_source(self) -> None:
        self._seed_brief_history()
        with self.assertRaises(ArtifactRollbackError):
            rollback_artifact(
                project=self.project,
                artifact_key="project_brief",
                source_version=3,
                actor="u",
            )


@override_settings(DRAMA_SKILLS_ROOT=str(SKILLS_ROOT))
class ArtifactRollbackApiTests(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="rollback_api", password="pass12345"
        )
        self.other = get_user_model().objects.create_user(
            username="rollback_other", password="pass12345"
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="回滚 API 测试",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="episode_plan",
            version=1,
            status=V3ArtifactVersion.Status.SUPERSEDED,
            payload={"episodes": [{"episode_number": 1}]},
        )
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="episode_plan",
            version=2,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload={"episodes": [{"episode_number": 1}, {"episode_number": 2}]},
        )
        self.client.force_authenticate(self.user)
        self.list_url = f"/api/v3/projects/{self.project.id}/artifacts/"
        self.rollback_url = f"/api/v3/projects/{self.project.id}/artifacts/rollback/"

    def test_list_requires_artifact_key(self) -> None:
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 400)
        self.assertNotEqual(resp.data.get("code"), 0)

    def test_list_ok(self) -> None:
        resp = self.client.get(self.list_url, {"artifact_key": "episode_plan"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        items = resp.data["data"]["items"]
        self.assertEqual([row["version"] for row in items], [2, 1])
        self.assertEqual(items[0]["status"], "committed")

    def test_list_rejects_disallowed_key(self) -> None:
        resp = self.client.get(self.list_url, {"artifact_key": "production_package"})
        self.assertEqual(resp.status_code, 400)

    def test_rollback_ok(self) -> None:
        resp = self.client.post(
            self.rollback_url,
            {"artifact_key": "episode_plan", "source_version": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["code"], 0)
        data = resp.data["data"]
        self.assertEqual(data["version"], 3)
        self.assertEqual(data["status"], "committed")
        self.assertEqual(len(data["payload"]["episodes"]), 1)

        latest = V3ArtifactVersion.objects.get(
            project=self.project,
            artifact_key="episode_plan",
            status=V3ArtifactVersion.Status.COMMITTED,
        )
        self.assertEqual(latest.version, 3)

    def test_rollback_missing_source(self) -> None:
        resp = self.client.post(
            self.rollback_url,
            {"artifact_key": "episode_plan", "source_version": 99},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_rollback_other_owner_404(self) -> None:
        self.client.force_authenticate(self.other)
        resp = self.client.post(
            self.rollback_url,
            {"artifact_key": "episode_plan", "source_version": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)
