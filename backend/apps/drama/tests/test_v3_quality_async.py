# -*- coding: utf-8 -*-
"""W4 Task 4：质检/交付 live 编排（Celery eager + mock LLM）。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3Project
from apps.drama.orchestrator import dispatch_command
from apps.drama.orchestrator.artifacts import latest
from apps.drama.orchestrator.report_meta import META_KEY, attach_script_meta, is_report_stale
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.skills_bridge.recipe_map import recipe_for
from apps.drama.tests.helpers import SKILLS_ROOT

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_BRIEF = json.loads(
    (_FIXTURES / "v3_project_brief_candidate.json").read_text(encoding="utf-8")
)
_BLUEPRINT = json.loads(
    (_FIXTURES / "v3_blueprint_bundle.json").read_text(encoding="utf-8")
)
_EPISODE_PLAN = json.loads(
    (_FIXTURES / "v3_episode_plan_candidate.json").read_text(encoding="utf-8")
)
_SCRIPTS = json.loads(
    (_FIXTURES / "v3_episode_scripts_candidate.json").read_text(encoding="utf-8")
)
_CHECKPOINT = json.loads(
    (_FIXTURES / "v3_memory_checkpoint_candidate.json").read_text(encoding="utf-8")
)
_QUALITY = json.loads((_FIXTURES / "v3_quality_report.json").read_text(encoding="utf-8"))
_COMPLIANCE = json.loads(
    (_FIXTURES / "v3_compliance_report.json").read_text(encoding="utf-8")
)
_PACKAGE = json.loads(
    (_FIXTURES / "v3_production_package.json").read_text(encoding="utf-8")
)
_BLUEPRINT_KEYS = recipe_for("generate_blueprint")["writes"]

_LLM_CALL_COUNT = {"n": 0}


def _mock_llm_call(prompt: str) -> str:
    _LLM_CALL_COUNT["n"] += 1
    if '"command_type": "score_quality"' in prompt:
        return json.dumps(_QUALITY, ensure_ascii=False)
    if '"command_type": "check_compliance"' in prompt:
        return json.dumps(_COMPLIANCE, ensure_ascii=False)
    if '"command_type": "revise_from_findings"' in prompt:
        return json.dumps(
            {
                "episode_scripts": _SCRIPTS,
                "memory_checkpoint": _CHECKPOINT,
            },
            ensure_ascii=False,
        )
    if '"command_type": "prepare_delivery"' in prompt:
        return json.dumps(_PACKAGE, ensure_ascii=False)
    raise AssertionError(f"unexpected LLM prompt fragment: {prompt[:160]}")


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    V3_LLM_CALL_OVERRIDE=_mock_llm_call,
)
class V3QualityAsyncTests(TestCase):
    def setUp(self) -> None:
        get_skills_loader.cache_clear()
        _LLM_CALL_COUNT["n"] = 0
        self.user = get_user_model().objects.create_user(
            username="quality_async_w4", password="pass12345"
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="质检编排项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.WRITING,
        )

    def _commit(self, key: str, payload: dict, *, version: int = 1) -> V3ArtifactVersion:
        return V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key=key,
            version=version,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=payload,
        )

    def _seed_writing_deps(self, *, script_version: int = 1) -> V3ArtifactVersion:
        self._commit("project_brief", _BRIEF)
        for key in _BLUEPRINT_KEYS:
            self._commit(key, _BLUEPRINT[key])
        self._commit("episode_plan", _EPISODE_PLAN)
        return self._commit(
            "episode_scripts", copy.deepcopy(_SCRIPTS), version=script_version
        )

    def _seed_passing_reports(self, scripts: V3ArtifactVersion) -> None:
        self._commit(
            "quality_report",
            attach_script_meta(copy.deepcopy(_QUALITY), script_art=scripts),
        )
        self._commit(
            "compliance_report",
            attach_script_meta(copy.deepcopy(_COMPLIANCE), script_art=scripts),
        )

    def test_score_and_compliance_commit_and_advance_stage(self) -> None:
        """1. 双报告 live → committed；writing→quality。"""
        scripts = self._seed_writing_deps()

        score = dispatch_command(
            owner=self.user,
            command_type="score_quality",
            payload={"project_id": str(self.project.id)},
        )
        score.refresh_from_db()
        self.assertEqual(score.status, V3CommandRun.Status.SUCCEEDED)
        quality = V3ArtifactVersion.objects.get(
            id=(score.result_payload.get("artifact_ids") or [])[0]
        )
        self.assertEqual(quality.artifact_key, "quality_report")
        self.assertEqual(quality.status, V3ArtifactVersion.Status.COMMITTED)
        self.assertEqual(
            quality.payload[META_KEY]["source_script_version"], scripts.version
        )

        compliance_run = dispatch_command(
            owner=self.user,
            command_type="check_compliance",
            payload={"project_id": str(self.project.id)},
        )
        compliance_run.refresh_from_db()
        self.assertEqual(compliance_run.status, V3CommandRun.Status.SUCCEEDED)
        compliance = V3ArtifactVersion.objects.get(
            id=(compliance_run.result_payload.get("artifact_ids") or [])[0]
        )
        self.assertEqual(compliance.artifact_key, "compliance_report")
        self.assertEqual(compliance.status, V3ArtifactVersion.Status.COMMITTED)

        self.project.refresh_from_db()
        self.assertEqual(self.project.stage, V3Project.Stage.QUALITY)

    def test_revise_confirm_makes_reports_stale(self) -> None:
        """2. revise→confirm 后正文升版 → 报告 stale（阻断交付）。"""
        scripts = self._seed_writing_deps(script_version=3)
        self._seed_passing_reports(scripts)
        self.project.stage = V3Project.Stage.QUALITY
        self.project.save(update_fields=["stage", "updated_at"])

        revise = dispatch_command(
            owner=self.user,
            command_type="revise_from_findings",
            payload={
                "project_id": str(self.project.id),
                "finding_keys": ["defect:0"],
            },
        )
        revise.refresh_from_db()
        self.assertEqual(revise.status, V3CommandRun.Status.SUCCEEDED)
        by_key = {
            art.artifact_key: art
            for art in V3ArtifactVersion.objects.filter(
                id__in=revise.result_payload.get("artifact_ids") or []
            )
        }
        self.assertEqual(
            by_key["episode_scripts"].status, V3ArtifactVersion.Status.CANDIDATE
        )

        confirm = dispatch_command(
            owner=self.user,
            command_type="confirm_script_candidate",
            payload={"project_id": str(self.project.id)},
        )
        self.assertEqual(confirm.status, V3CommandRun.Status.SUCCEEDED)

        new_scripts = latest(
            self.project,
            "episode_scripts",
            status=V3ArtifactVersion.Status.COMMITTED,
        )
        assert new_scripts is not None
        self.assertGreater(new_scripts.version, scripts.version)

        quality = latest(
            self.project,
            "quality_report",
            status=V3ArtifactVersion.Status.COMMITTED,
        )
        compliance = latest(
            self.project,
            "compliance_report",
            status=V3ArtifactVersion.Status.COMMITTED,
        )
        assert quality is not None and compliance is not None
        self.assertTrue(
            is_report_stale(report_payload=quality.payload, current_script=new_scripts)
        )
        self.assertTrue(
            is_report_stale(
                report_payload=compliance.payload, current_script=new_scripts
            )
        )

        prep = dispatch_command(
            owner=self.user,
            command_type="prepare_delivery",
            payload={"project_id": str(self.project.id)},
        )
        prep.refresh_from_db()
        self.assertEqual(prep.status, V3CommandRun.Status.FAILED)
        self.assertIn("质量报告", prep.error_message)
        self.assertNotIn("Traceback", prep.error_message)

    def test_prepare_delivery_gate_fail_skips_llm(self) -> None:
        """3. 门禁失败 → failed 中文 blockers，不调 LLM，无 package。"""
        self._seed_writing_deps()
        before = _LLM_CALL_COUNT["n"]

        run = dispatch_command(
            owner=self.user,
            command_type="prepare_delivery",
            payload={"project_id": str(self.project.id)},
        )
        run.refresh_from_db()
        self.assertEqual(run.status, V3CommandRun.Status.FAILED)
        self.assertTrue(run.error_message)
        self.assertIn("质量报告", run.error_message)
        self.assertEqual(_LLM_CALL_COUNT["n"], before)
        self.assertFalse(
            V3ArtifactVersion.objects.filter(
                project=self.project, artifact_key="production_package"
            ).exists()
        )

    def test_prepare_delivery_gate_success_commits_and_stage(self) -> None:
        """4. 门禁通过 → package committed；stage=delivery。"""
        scripts = self._seed_writing_deps(script_version=2)
        self._seed_passing_reports(scripts)
        self.project.stage = V3Project.Stage.QUALITY
        self.project.save(update_fields=["stage", "updated_at"])

        run = dispatch_command(
            owner=self.user,
            command_type="prepare_delivery",
            payload={"project_id": str(self.project.id)},
        )
        run.refresh_from_db()
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        art = V3ArtifactVersion.objects.get(
            id=(run.result_payload.get("artifact_ids") or [])[0]
        )
        self.assertEqual(art.artifact_key, "production_package")
        self.assertEqual(art.status, V3ArtifactVersion.Status.COMMITTED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.stage, V3Project.Stage.DELIVERY)
