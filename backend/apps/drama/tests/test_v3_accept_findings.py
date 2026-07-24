# -*- coding: utf-8 -*-
"""W4 Task 4：accept_findings 同步 upsert。"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.drama.models import V3CommandRun, V3Project, V3QualityFinding
from apps.drama.orchestrator import dispatch_command


class AcceptFindingsTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="accept_findings_u", password="pass12345"
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="接受问题项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.QUALITY,
        )

    def test_accept_findings_upserts_accepted(self) -> None:
        """accept → status=accepted；同 key 再 accept 为 upsert。"""
        run = dispatch_command(
            owner=self.user,
            command_type="accept_findings",
            payload={
                "project_id": str(self.project.id),
                "findings": [
                    {
                        "source": "compliance",
                        "finding_key": "blk-1",
                        "title": "敏感用语",
                        "severity": "high",
                    }
                ],
            },
        )
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        finding = V3QualityFinding.objects.get(
            project=self.project,
            source=V3QualityFinding.Source.COMPLIANCE,
            finding_key="blk-1",
        )
        self.assertEqual(finding.status, V3QualityFinding.Status.ACCEPTED)
        self.assertEqual(finding.title, "敏感用语")
        self.assertEqual(finding.severity, "high")
        accepted_ids = (run.result_payload or {}).get("finding_ids") or []
        self.assertEqual(accepted_ids, [str(finding.id)])

        again = dispatch_command(
            owner=self.user,
            command_type="accept_findings",
            payload={
                "project_id": str(self.project.id),
                "findings": [
                    {
                        "source": "compliance",
                        "finding_key": "blk-1",
                        "title": "敏感用语（已阅）",
                        "severity": "medium",
                    }
                ],
            },
        )
        self.assertEqual(again.status, V3CommandRun.Status.SUCCEEDED)
        self.assertEqual(
            V3QualityFinding.objects.filter(project=self.project).count(), 1
        )
        finding.refresh_from_db()
        self.assertEqual(finding.title, "敏感用语（已阅）")
        self.assertEqual(finding.severity, "medium")
        self.assertEqual(finding.status, V3QualityFinding.Status.ACCEPTED)

    def test_accept_findings_rejects_invalid_payload(self) -> None:
        run = dispatch_command(
            owner=self.user,
            command_type="accept_findings",
            payload={"project_id": str(self.project.id), "findings": []},
        )
        self.assertEqual(run.status, V3CommandRun.Status.FAILED)
        self.assertTrue(run.error_message)
        self.assertNotIn("Traceback", run.error_message)
