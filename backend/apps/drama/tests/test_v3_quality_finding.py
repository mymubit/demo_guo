# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.drama.models import V3ArtifactVersion, V3Project, V3QualityFinding


class V3QualityFindingTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="qf_u", password="pass12345")
        self.project = V3Project.objects.create(
            owner=self.user,
            title="Quality Finding Test",
            entry_type=V3Project.EntryType.ORIGINAL,
        )

    def test_create_quality_finding(self) -> None:
        finding = V3QualityFinding.objects.create(
            project=self.project,
            source=V3QualityFinding.Source.QUALITY,
            finding_key="defect:0",
            title="节奏偏慢",
            severity="medium",
        )
        self.assertEqual(finding.project_id, self.project.id)
        self.assertEqual(finding.source, V3QualityFinding.Source.QUALITY)
        self.assertEqual(finding.finding_key, "defect:0")
        self.assertEqual(finding.status, V3QualityFinding.Status.OPEN)
        self.assertIsNone(finding.report_artifact_id)
        self.assertIsNotNone(finding.created_at)
        self.assertIsNotNone(finding.updated_at)

    def test_unique_project_source_finding_key(self) -> None:
        V3QualityFinding.objects.create(
            project=self.project,
            source=V3QualityFinding.Source.COMPLIANCE,
            finding_key="block:1",
            title="敏感词",
        )
        with self.assertRaises(IntegrityError):
            V3QualityFinding.objects.create(
                project=self.project,
                source=V3QualityFinding.Source.COMPLIANCE,
                finding_key="block:1",
                title="重复键",
            )

    def test_same_key_different_source_allowed(self) -> None:
        V3QualityFinding.objects.create(
            project=self.project,
            source=V3QualityFinding.Source.QUALITY,
            finding_key="issue:1",
            title="质量侧",
        )
        other = V3QualityFinding.objects.create(
            project=self.project,
            source=V3QualityFinding.Source.COMPLIANCE,
            finding_key="issue:1",
            title="合规侧",
        )
        self.assertEqual(other.finding_key, "issue:1")
        self.assertEqual(V3QualityFinding.objects.filter(project=self.project).count(), 2)

    def test_report_artifact_optional_fk(self) -> None:
        art = V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="quality_report",
            version=1,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload={"grade": "A"},
        )
        finding = V3QualityFinding.objects.create(
            project=self.project,
            source=V3QualityFinding.Source.QUALITY,
            finding_key="defect:2",
            title="对白重复",
            report_artifact=art,
        )
        self.assertEqual(finding.report_artifact_id, art.id)
