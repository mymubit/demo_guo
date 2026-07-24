# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3Project
from apps.drama.orchestrator.artifacts import latest, next_version


class V3ArtifactVersionTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="artu", password="pass12345")
        self.project = V3Project.objects.create(
            owner=self.user,
            title="Artifact Test",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        self.run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic",
            status=V3CommandRun.Status.SUCCEEDED,
        )

    def test_create_candidate_artifact(self) -> None:
        artifact = V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=1,
            status=V3ArtifactVersion.Status.CANDIDATE,
            payload={"title": "测试选题"},
            command_run=self.run,
        )
        self.assertEqual(artifact.artifact_key, "project_brief")
        self.assertEqual(artifact.status, V3ArtifactVersion.Status.CANDIDATE)
        self.assertEqual(artifact.payload["title"], "测试选题")
        self.assertEqual(artifact.command_run_id, self.run.id)

    def test_unique_project_key_version(self) -> None:
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=1,
            status=V3ArtifactVersion.Status.CANDIDATE,
            payload={},
        )
        with self.assertRaises(IntegrityError):
            V3ArtifactVersion.objects.create(
                project=self.project,
                artifact_key="project_brief",
                version=1,
                status=V3ArtifactVersion.Status.DRAFT,
                payload={},
            )

    def test_next_version_starts_at_one(self) -> None:
        self.assertEqual(next_version(self.project.id, "project_brief"), 1)

    def test_next_version_increments(self) -> None:
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=1,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload={},
        )
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=3,
            status=V3ArtifactVersion.Status.CANDIDATE,
            payload={},
        )
        self.assertEqual(next_version(self.project.id, "project_brief"), 4)

    def test_latest_returns_highest_version(self) -> None:
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=1,
            status=V3ArtifactVersion.Status.SUPERSEDED,
            payload={"v": 1},
        )
        v2 = V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=2,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload={"v": 2},
        )
        found = latest(self.project, "project_brief")
        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found.id, v2.id)
        self.assertEqual(found.version, 2)

    def test_latest_filters_by_status(self) -> None:
        V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=1,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload={},
        )
        candidate = V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="project_brief",
            version=2,
            status=V3ArtifactVersion.Status.CANDIDATE,
            payload={},
        )
        found = latest(self.project, "project_brief", status=V3ArtifactVersion.Status.CANDIDATE)
        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found.id, candidate.id)
