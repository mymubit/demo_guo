# -*- coding: utf-8 -*-
"""W4 Task 3：executor commit_mode=direct|candidate（质检/修订）。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3Project
from apps.drama.orchestrator.report_meta import META_KEY, is_report_stale
from apps.drama.orchestrator.system_config import save_system_overlay
from apps.drama.services.skills_loader import get_skills_loader
from apps.drama.skills_bridge.executor import execute_generation
from apps.drama.skills_bridge.validate import validate_artifact_payload
from apps.drama.tests.helpers import SKILLS_ROOT

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_BRIEF_PATH = _FIXTURES / "v3_project_brief_candidate.json"
_BLUEPRINT_PATH = _FIXTURES / "v3_blueprint_bundle.json"
_EPISODE_PLAN_PATH = _FIXTURES / "v3_episode_plan_candidate.json"
_EPISODE_SCRIPTS_PATH = _FIXTURES / "v3_episode_scripts_candidate.json"
_MEMORY_CHECKPOINT_PATH = _FIXTURES / "v3_memory_checkpoint_candidate.json"
_QUALITY_PATH = _FIXTURES / "v3_quality_report.json"
_COMPLIANCE_PATH = _FIXTURES / "v3_compliance_report.json"
_PACKAGE_PATH = _FIXTURES / "v3_production_package.json"


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class QualityExecutorDirectCommitTests(TestCase):
    def setUp(self) -> None:
        get_skills_loader.cache_clear()
        self.user = get_user_model().objects.create_user(
            username="q_exec", password="pass12345"
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="质检执行器项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.WRITING,
        )
        self.brief = json.loads(_BRIEF_PATH.read_text(encoding="utf-8"))
        self.blueprint = json.loads(_BLUEPRINT_PATH.read_text(encoding="utf-8"))
        self.episode_plan = json.loads(_EPISODE_PLAN_PATH.read_text(encoding="utf-8"))
        self.scripts = json.loads(_EPISODE_SCRIPTS_PATH.read_text(encoding="utf-8"))
        self.checkpoint = json.loads(
            _MEMORY_CHECKPOINT_PATH.read_text(encoding="utf-8")
        )
        self.quality = json.loads(_QUALITY_PATH.read_text(encoding="utf-8"))
        self.compliance = json.loads(_COMPLIANCE_PATH.read_text(encoding="utf-8"))
        self.package = json.loads(_PACKAGE_PATH.read_text(encoding="utf-8"))

    def _commit(self, key: str, payload: dict, *, version: int = 1) -> V3ArtifactVersion:
        return V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key=key,
            version=version,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=payload,
        )

    def _seed_score_deps(self) -> V3ArtifactVersion:
        self._commit("project_brief", self.brief)
        self._commit("story_bible", self.blueprint["story_bible"])
        self._commit("episode_plan", self.episode_plan)
        return self._commit("episode_scripts", self.scripts, version=3)

    def test_score_quality_writes_committed_with_meta(self) -> None:
        scripts = self._seed_score_deps()
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="score_quality",
            status=V3CommandRun.Status.RUNNING,
        )

        def fake_llm(_prompt: str) -> str:
            return json.dumps(self.quality, ensure_ascii=False)

        created = execute_generation(
            command_type="score_quality",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        self.assertEqual(len(created), 1)
        art = created[0]
        self.assertEqual(art.artifact_key, "quality_report")
        self.assertEqual(art.status, V3ArtifactVersion.Status.COMMITTED)
        self.assertEqual(art.command_run_id, run.id)
        self.assertEqual(
            art.payload[META_KEY],
            {
                "source_script_version": scripts.version,
                "source_script_artifact_id": str(scripts.id),
            },
        )
        self.assertFalse(
            is_report_stale(report_payload=art.payload, current_script=scripts)
        )
        # 落库含 meta，剥离后仍应通过 schema
        from apps.drama.orchestrator.report_meta import strip_meta_for_validate

        self.assertEqual(
            validate_artifact_payload(
                "quality_report", strip_meta_for_validate(art.payload)
            ),
            [],
        )

    def test_score_and_compliance_prompt_inject_system_config(self) -> None:
        """score/compliance/prepare_delivery prompt 注入 effective system_config。"""
        save_system_overlay(
            overlay={
                "target_platform": "douyin",
                "scoring_preset": "rhythm_first",
            },
            actor="ops",
        )
        scripts = self._seed_score_deps()
        self._commit(
            "quality_report",
            {
                **copy.deepcopy(self.quality),
                META_KEY: {"source_script_version": scripts.version},
            },
        )
        self._commit(
            "compliance_report",
            {
                **copy.deepcopy(self.compliance),
                META_KEY: {"source_script_version": scripts.version},
            },
        )
        captured: list[str] = []

        def capturing_llm(prompt: str) -> str:
            captured.append(prompt)
            if '"command_type": "score_quality"' in prompt:
                return json.dumps(self.quality, ensure_ascii=False)
            if '"command_type": "check_compliance"' in prompt:
                return json.dumps(self.compliance, ensure_ascii=False)
            if '"command_type": "prepare_delivery"' in prompt:
                return json.dumps(self.package, ensure_ascii=False)
            raise AssertionError(f"unexpected prompt: {prompt[:160]}")

        for command_type in ("score_quality", "check_compliance", "prepare_delivery"):
            run = V3CommandRun.objects.create(
                owner=self.user,
                project=self.project,
                command_type=command_type,
                status=V3CommandRun.Status.RUNNING,
            )
            execute_generation(
                command_type=command_type,
                project=self.project,
                run=run,
                llm_call=capturing_llm,
            )

        self.assertEqual(len(captured), 3)
        for prompt in captured:
            self.assertIn('"scoring_preset": "rhythm_first"', prompt)
            self.assertIn('"target_platform": "douyin"', prompt)
            self.assertIn('"system_config"', prompt)

    def test_score_quality_strips_llm_meta_before_validate(self) -> None:
        scripts = self._seed_score_deps()
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="score_quality",
            status=V3CommandRun.Status.RUNNING,
        )
        polluted = copy.deepcopy(self.quality)
        polluted[META_KEY] = {
            "source_script_version": 999,
            "source_script_artifact_id": "deadbeef",
        }

        def fake_llm(_prompt: str) -> str:
            return json.dumps(polluted, ensure_ascii=False)

        created = execute_generation(
            command_type="score_quality",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        art = created[0]
        self.assertEqual(art.payload[META_KEY]["source_script_version"], scripts.version)
        self.assertEqual(
            art.payload[META_KEY]["source_script_artifact_id"], str(scripts.id)
        )

    def test_direct_supersedes_old_committed_and_candidate(self) -> None:
        scripts = self._seed_score_deps()
        old_committed = self._commit(
            "quality_report",
            copy.deepcopy(self.quality),
            version=1,
        )
        old_candidate = V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key="quality_report",
            version=2,
            status=V3ArtifactVersion.Status.CANDIDATE,
            payload=copy.deepcopy(self.quality),
        )
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="score_quality",
            status=V3CommandRun.Status.RUNNING,
        )

        def fake_llm(_prompt: str) -> str:
            return json.dumps(self.quality, ensure_ascii=False)

        created = execute_generation(
            command_type="score_quality",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        self.assertEqual(len(created), 1)
        new_art = created[0]
        self.assertEqual(new_art.status, V3ArtifactVersion.Status.COMMITTED)
        old_committed.refresh_from_db()
        old_candidate.refresh_from_db()
        self.assertEqual(old_committed.status, V3ArtifactVersion.Status.SUPERSEDED)
        self.assertEqual(old_candidate.status, V3ArtifactVersion.Status.SUPERSEDED)
        self.assertEqual(
            V3ArtifactVersion.objects.filter(
                project=self.project,
                artifact_key="quality_report",
                status=V3ArtifactVersion.Status.COMMITTED,
            ).count(),
            1,
        )
        self.assertEqual(
            new_art.payload[META_KEY]["source_script_version"], scripts.version
        )

    def test_check_compliance_direct_commit(self) -> None:
        scripts = self._seed_score_deps()
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="check_compliance",
            status=V3CommandRun.Status.RUNNING,
        )

        def fake_llm(_prompt: str) -> str:
            return json.dumps(self.compliance, ensure_ascii=False)

        created = execute_generation(
            command_type="check_compliance",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        art = created[0]
        self.assertEqual(art.artifact_key, "compliance_report")
        self.assertEqual(art.status, V3ArtifactVersion.Status.COMMITTED)
        self.assertEqual(
            art.payload[META_KEY]["source_script_version"], scripts.version
        )

    def test_revise_from_findings_still_candidate(self) -> None:
        self._seed_score_deps()
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="revise_from_findings",
            status=V3CommandRun.Status.RUNNING,
        )

        def fake_llm(_prompt: str) -> str:
            return json.dumps(
                {
                    "episode_scripts": self.scripts,
                    "memory_checkpoint": self.checkpoint,
                },
                ensure_ascii=False,
            )

        created = execute_generation(
            command_type="revise_from_findings",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        self.assertEqual(len(created), 2)
        by_key = {item.artifact_key: item for item in created}
        self.assertEqual(
            by_key["episode_scripts"].status, V3ArtifactVersion.Status.CANDIDATE
        )
        self.assertEqual(
            by_key["memory_checkpoint"].status, V3ArtifactVersion.Status.CANDIDATE
        )
        self.assertNotIn(META_KEY, by_key["episode_scripts"].payload)

    def test_prepare_delivery_direct_commit(self) -> None:
        scripts = self._seed_score_deps()
        self._commit(
            "quality_report",
            {**copy.deepcopy(self.quality), META_KEY: {"source_script_version": 3}},
        )
        self._commit(
            "compliance_report",
            {
                **copy.deepcopy(self.compliance),
                META_KEY: {"source_script_version": 3},
            },
        )
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="prepare_delivery",
            status=V3CommandRun.Status.RUNNING,
        )

        def fake_llm(_prompt: str) -> str:
            return json.dumps(self.package, ensure_ascii=False)

        created = execute_generation(
            command_type="prepare_delivery",
            project=self.project,
            run=run,
            llm_call=fake_llm,
        )
        art = created[0]
        self.assertEqual(art.artifact_key, "production_package")
        self.assertEqual(art.status, V3ArtifactVersion.Status.COMMITTED)
        self.assertEqual(
            art.payload[META_KEY]["source_script_version"], scripts.version
        )
