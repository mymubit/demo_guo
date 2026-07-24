# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from apps.drama.models import V3ArtifactVersion, V3Project
from apps.drama.orchestrator.report_meta import (
    META_KEY,
    attach_script_meta,
    is_report_stale,
    read_source_script_version,
    strip_meta_for_validate,
)


class ReportMetaUnitTests(SimpleTestCase):
    def test_strip_meta_for_validate_removes_key(self) -> None:
        payload = {"grade": "A", META_KEY: {"source_script_version": 2}}
        cleaned = strip_meta_for_validate(payload)
        self.assertEqual(cleaned, {"grade": "A"})
        self.assertIn(META_KEY, payload)

    def test_read_source_script_version(self) -> None:
        self.assertEqual(
            read_source_script_version({META_KEY: {"source_script_version": 3}}),
            3,
        )
        self.assertIsNone(read_source_script_version({}))
        self.assertIsNone(read_source_script_version({META_KEY: {}}))


class ReportMetaStaleTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="rm_u", password="pass12345")
        self.project = V3Project.objects.create(
            owner=self.user,
            title="Report Meta Test",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        self.script_v3 = V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="episode_scripts",
            version=3,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload={"episodes": []},
        )

    def test_attach_script_meta_shape(self) -> None:
        payload = {"grade": "B"}
        out = attach_script_meta(payload, script_art=self.script_v3)
        self.assertEqual(out["grade"], "B")
        self.assertEqual(
            out[META_KEY],
            {
                "source_script_version": 3,
                "source_script_artifact_id": str(self.script_v3.id),
            },
        )
        self.assertNotIn(META_KEY, payload)

    def test_is_report_stale_false_when_versions_match(self) -> None:
        report = attach_script_meta({"verdict": "通过"}, script_art=self.script_v3)
        self.assertFalse(
            is_report_stale(report_payload=report, current_script=self.script_v3)
        )

    def test_is_report_stale_true_when_script_upgraded(self) -> None:
        report = attach_script_meta({"verdict": "通过"}, script_art=self.script_v3)
        script_v4 = V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="episode_scripts",
            version=4,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload={"episodes": []},
        )
        self.assertTrue(is_report_stale(report_payload=report, current_script=script_v4))

    def test_is_report_stale_true_when_no_current_script(self) -> None:
        report = attach_script_meta({"verdict": "通过"}, script_art=self.script_v3)
        self.assertTrue(is_report_stale(report_payload=report, current_script=None))

    def test_is_report_stale_true_when_meta_missing(self) -> None:
        self.assertTrue(
            is_report_stale(report_payload={"verdict": "通过"}, current_script=self.script_v3)
        )
