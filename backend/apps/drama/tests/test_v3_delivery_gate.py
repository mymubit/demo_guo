# -*- coding: utf-8 -*-
"""W4 Task 3：delivery_gate 门禁判定。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.drama.models import V3ArtifactVersion, V3Project, V3QualityFinding
from apps.drama.orchestrator.delivery_gate import evaluate_delivery_gate
from apps.drama.orchestrator.report_meta import attach_script_meta

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_QUALITY_PATH = _FIXTURES / "v3_quality_report.json"
_COMPLIANCE_PATH = _FIXTURES / "v3_compliance_report.json"


class DeliveryGateTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="gate_u", password="pass12345"
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="门禁测试项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.QUALITY,
        )
        self.quality_payload = json.loads(_QUALITY_PATH.read_text(encoding="utf-8"))
        self.compliance_payload = json.loads(
            _COMPLIANCE_PATH.read_text(encoding="utf-8")
        )

    def _commit(
        self, key: str, payload: dict, *, version: int = 1
    ) -> V3ArtifactVersion:
        return V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key=key,
            version=version,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=payload,
        )

    def _commit_scripts(self, *, version: int = 1) -> V3ArtifactVersion:
        return self._commit(
            "episode_scripts",
            {"episodes": [{"episode_number": 1, "title": "测"}]},
            version=version,
        )

    def _seed_passing_reports(self, scripts: V3ArtifactVersion) -> None:
        self._commit(
            "quality_report",
            attach_script_meta(copy.deepcopy(self.quality_payload), script_art=scripts),
        )
        self._commit(
            "compliance_report",
            attach_script_meta(
                copy.deepcopy(self.compliance_payload), script_art=scripts
            ),
        )

    def test_missing_scripts_blocks(self) -> None:
        result = evaluate_delivery_gate(self.project)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blockers"], ["请先确认正文后再交付"])

    def test_missing_quality_report_blocks(self) -> None:
        scripts = self._commit_scripts()
        self._commit(
            "compliance_report",
            attach_script_meta(
                copy.deepcopy(self.compliance_payload), script_art=scripts
            ),
        )
        result = evaluate_delivery_gate(self.project)
        self.assertFalse(result["passed"])
        self.assertIn("需要有效的质量报告，请重新评分", result["blockers"])

    def test_stale_quality_report_blocks(self) -> None:
        scripts_v1 = self._commit_scripts(version=1)
        self._commit(
            "quality_report",
            attach_script_meta(
                copy.deepcopy(self.quality_payload), script_art=scripts_v1
            ),
        )
        self._commit(
            "compliance_report",
            attach_script_meta(
                copy.deepcopy(self.compliance_payload), script_art=scripts_v1
            ),
        )
        self._commit_scripts(version=2)
        result = evaluate_delivery_gate(self.project)
        self.assertFalse(result["passed"])
        self.assertIn("需要有效的质量报告，请重新评分", result["blockers"])

    def test_quality_fail_blocks(self) -> None:
        scripts = self._commit_scripts()
        bad_quality = copy.deepcopy(self.quality_payload)
        bad_quality["verdict"] = "不通过"
        bad_quality["grade"] = "C"
        bad_quality["needs_revision"] = True
        self._commit(
            "quality_report",
            attach_script_meta(bad_quality, script_art=scripts),
        )
        self._commit(
            "compliance_report",
            attach_script_meta(
                copy.deepcopy(self.compliance_payload), script_art=scripts
            ),
        )
        result = evaluate_delivery_gate(self.project)
        self.assertFalse(result["passed"])
        self.assertIn("质量报告未通过门禁", result["blockers"])

    def test_quality_passes_via_grade_band(self) -> None:
        scripts = self._commit_scripts()
        quality = copy.deepcopy(self.quality_payload)
        quality["verdict"] = "待修订"
        quality["grade"] = "B"
        quality["needs_revision"] = False
        self._commit("quality_report", attach_script_meta(quality, script_art=scripts))
        self._commit(
            "compliance_report",
            attach_script_meta(
                copy.deepcopy(self.compliance_payload), script_art=scripts
            ),
        )
        result = evaluate_delivery_gate(self.project)
        self.assertTrue(result["passed"])
        self.assertEqual(result["blockers"], [])

    def test_compliance_fail_blocks(self) -> None:
        scripts = self._commit_scripts()
        self._commit(
            "quality_report",
            attach_script_meta(copy.deepcopy(self.quality_payload), script_art=scripts),
        )
        bad_compliance = copy.deepcopy(self.compliance_payload)
        bad_compliance["overall_result"] = "不通过"
        self._commit(
            "compliance_report",
            attach_script_meta(bad_compliance, script_art=scripts),
        )
        result = evaluate_delivery_gate(self.project)
        self.assertFalse(result["passed"])
        self.assertIn("合规审查未通过", result["blockers"])

    def test_unaccepted_blocking_issues_block(self) -> None:
        scripts = self._commit_scripts()
        self._commit(
            "quality_report",
            attach_script_meta(copy.deepcopy(self.quality_payload), script_art=scripts),
        )
        compliance = copy.deepcopy(self.compliance_payload)
        compliance["blocking_issues"] = [
            {"finding_key": "blk-1", "title": "敏感用语", "description": "需处理"}
        ]
        self._commit(
            "compliance_report",
            attach_script_meta(compliance, script_art=scripts),
        )
        result = evaluate_delivery_gate(self.project)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("未接受" in item or "阻断" in item for item in result["blockers"])
        )

    def test_accepted_blocking_issues_allow_pass(self) -> None:
        scripts = self._commit_scripts()
        self._seed_passing_reports(scripts)
        # 覆盖合规：带 blocking_issues 但已 accepted
        compliance = copy.deepcopy(self.compliance_payload)
        compliance["blocking_issues"] = [
            {"finding_key": "blk-1", "title": "敏感用语", "description": "需处理"}
        ]
        V3ArtifactVersion.objects.filter(
            project=self.project, artifact_key="compliance_report"
        ).update(payload=attach_script_meta(compliance, script_art=scripts))
        V3QualityFinding.objects.create(
            project=self.project,
            source=V3QualityFinding.Source.COMPLIANCE,
            finding_key="blk-1",
            title="敏感用语",
            status=V3QualityFinding.Status.ACCEPTED,
        )
        result = evaluate_delivery_gate(self.project)
        self.assertTrue(result["passed"])
        self.assertEqual(result["blockers"], [])

    def test_empty_blocking_issues_skipped(self) -> None:
        scripts = self._commit_scripts()
        self._seed_passing_reports(scripts)
        result = evaluate_delivery_gate(self.project)
        self.assertTrue(result["passed"])
        self.assertEqual(result["blockers"], [])

    def test_all_green_passes(self) -> None:
        scripts = self._commit_scripts()
        self._seed_passing_reports(scripts)
        result = evaluate_delivery_gate(self.project)
        self.assertEqual(result, {"passed": True, "blockers": []})
