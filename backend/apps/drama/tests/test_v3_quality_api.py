# -*- coding: utf-8 -*-
"""V3 W4：Quality REST API（eager + mock LLM）。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.models import V3ArtifactVersion, V3Project, V3QualityFinding
from apps.drama.orchestrator.report_meta import META_KEY, attach_script_meta
from apps.drama.skills_bridge.recipe_map import recipe_for
from apps.drama.tests.helpers import SKILLS_ROOT

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
_BRIEF = json.loads(
    (_FIXTURE_DIR / "v3_project_brief_candidate.json").read_text(encoding="utf-8")
)
_BLUEPRINT = json.loads(
    (_FIXTURE_DIR / "v3_blueprint_bundle.json").read_text(encoding="utf-8")
)
_EPISODE_PLAN = json.loads(
    (_FIXTURE_DIR / "v3_episode_plan_candidate.json").read_text(encoding="utf-8")
)
_SCRIPTS = json.loads(
    (_FIXTURE_DIR / "v3_episode_scripts_candidate.json").read_text(encoding="utf-8")
)
_CHECKPOINT = json.loads(
    (_FIXTURE_DIR / "v3_memory_checkpoint_candidate.json").read_text(encoding="utf-8")
)
_QUALITY = json.loads(
    (_FIXTURE_DIR / "v3_quality_report.json").read_text(encoding="utf-8")
)
_COMPLIANCE = json.loads(
    (_FIXTURE_DIR / "v3_compliance_report.json").read_text(encoding="utf-8")
)
_BLUEPRINT_KEYS = recipe_for("generate_blueprint")["writes"]


def _mock_llm_call(prompt: str) -> str:
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
    raise AssertionError(f"unexpected LLM prompt fragment: {prompt[:160]}")


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    V3_LLM_CALL_OVERRIDE=_mock_llm_call,
)
class V3QualityApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="quality_api", password="pass12345"
        )
        self.other = user_model.objects.create_user(
            username="quality_other", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.project = V3Project.objects.create(
            owner=self.user,
            title="质检 API 项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.QUALITY,
        )
        self.base = f"/api/v3/projects/{self.project.id}/quality"
        self.scripts = self._seed_committed_deps()

    def _commit(self, key: str, payload: dict, *, version: int = 1) -> V3ArtifactVersion:
        return V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key=key,
            version=version,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=payload,
        )

    def _seed_committed_deps(self) -> V3ArtifactVersion:
        self._commit("project_brief", _BRIEF)
        for key in _BLUEPRINT_KEYS:
            self._commit(key, _BLUEPRINT[key])
        self._commit("episode_plan", _EPISODE_PLAN)
        return self._commit("episode_scripts", copy.deepcopy(_SCRIPTS))

    def test_get_empty_quality_state(self) -> None:
        resp = self.client.get(f"{self.base}/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(data["stage"], "quality")
        self.assertIsNone(data["quality_report"])
        self.assertIsNone(data["compliance_report"])
        self.assertEqual(data["findings"], [])
        self.assertFalse(data["quality_is_stale"])
        self.assertFalse(data["compliance_is_stale"])
        self.assertIsNone(data["latest_quality_run"])
        self.assertIsNone(data["latest_compliance_run"])

    def test_get_reports_findings_and_stale_flags(self) -> None:
        self._commit(
            "quality_report",
            attach_script_meta(copy.deepcopy(_QUALITY), script_art=self.scripts),
        )
        stale_compliance = attach_script_meta(
            copy.deepcopy(_COMPLIANCE), script_art=self.scripts
        )
        stale_compliance[META_KEY]["source_script_version"] = 99
        self._commit("compliance_report", stale_compliance)
        V3QualityFinding.objects.create(
            project=self.project,
            source=V3QualityFinding.Source.COMPLIANCE,
            finding_key="blk-1",
            title="敏感用语",
            severity="high",
            status=V3QualityFinding.Status.ACCEPTED,
        )

        resp = self.client.get(f"{self.base}/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["quality_report"]["artifact_key"], "quality_report")
        self.assertEqual(data["compliance_report"]["artifact_key"], "compliance_report")
        self.assertFalse(data["quality_is_stale"])
        self.assertTrue(data["compliance_is_stale"])
        self.assertEqual(len(data["findings"]), 1)
        self.assertEqual(data["findings"][0]["finding_key"], "blk-1")
        self.assertEqual(data["findings"][0]["source"], "compliance")
        self.assertEqual(data["findings"][0]["status"], "accepted")

    def test_score_and_compliance_dispatch(self) -> None:
        score = self.client.post(f"{self.base}/score/", {}, format="json")
        self.assertEqual(score.status_code, 200)
        score_run = score.json()["data"]["command_run"]
        self.assertEqual(score_run["command_type"], "score_quality")
        self.assertEqual(score_run["status"], "succeeded")
        self.assertNotIn("Traceback", score_run.get("error_message") or "")

        compliance = self.client.post(f"{self.base}/compliance/", {}, format="json")
        self.assertEqual(compliance.status_code, 200)
        compliance_run = compliance.json()["data"]["command_run"]
        self.assertEqual(compliance_run["command_type"], "check_compliance")
        self.assertEqual(compliance_run["status"], "succeeded")

        state = self.client.get(f"{self.base}/").json()["data"]
        self.assertIsNotNone(state["quality_report"])
        self.assertEqual(state["quality_report"]["status"], "committed")
        self.assertIsNotNone(state["compliance_report"])
        self.assertEqual(state["compliance_report"]["status"], "committed")
        self.assertFalse(state["quality_is_stale"])
        self.assertFalse(state["compliance_is_stale"])
        self.assertEqual(state["latest_quality_run"]["id"], score_run["id"])
        self.assertEqual(state["latest_compliance_run"]["id"], compliance_run["id"])

    def test_accept_findings_upserts(self) -> None:
        resp = self.client.post(
            f"{self.base}/accept/",
            {
                "findings": [
                    {
                        "source": "compliance",
                        "finding_key": "blk-1",
                        "title": "敏感用语",
                        "severity": "high",
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        run = resp.json()["data"]["command_run"]
        self.assertEqual(run["command_type"], "accept_findings")
        self.assertEqual(run["status"], "succeeded")
        self.assertEqual(len(run["result_payload"]["finding_ids"]), 1)

        finding = V3QualityFinding.objects.get(
            project=self.project,
            source=V3QualityFinding.Source.COMPLIANCE,
            finding_key="blk-1",
        )
        self.assertEqual(finding.status, V3QualityFinding.Status.ACCEPTED)

        state = self.client.get(f"{self.base}/").json()["data"]
        self.assertEqual(len(state["findings"]), 1)
        self.assertEqual(state["latest_quality_run"]["id"], run["id"])

    def test_accept_requires_findings(self) -> None:
        resp = self.client.post(f"{self.base}/accept/", {}, format="json")
        self.assertEqual(resp.status_code, 400)

        empty = self.client.post(
            f"{self.base}/accept/", {"findings": []}, format="json"
        )
        self.assertEqual(empty.status_code, 400)

    def test_revise_from_findings_creates_candidate(self) -> None:
        revise = self.client.post(
            f"{self.base}/revise/",
            {
                "finding_keys": ["defect:0"],
                "episode_range": {"start": 1, "end": 1},
            },
            format="json",
        )
        self.assertEqual(revise.status_code, 200)
        run = revise.json()["data"]["command_run"]
        self.assertEqual(run["command_type"], "revise_from_findings")
        self.assertEqual(run["status"], "succeeded")
        self.assertNotIn("Traceback", run.get("error_message") or "")

        candidate = V3ArtifactVersion.objects.filter(
            project=self.project,
            artifact_key="episode_scripts",
            status=V3ArtifactVersion.Status.CANDIDATE,
        ).first()
        self.assertIsNotNone(candidate)

        state = self.client.get(f"{self.base}/").json()["data"]
        self.assertEqual(state["latest_quality_run"]["id"], run["id"])

    def test_revise_invalid_episode_range(self) -> None:
        resp = self.client.post(
            f"{self.base}/revise/",
            {"episode_range": {"start": 3, "end": 1}},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_owner_isolation_returns_404(self) -> None:
        foreign = V3Project.objects.create(
            owner=self.other,
            title="他人质检",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        paths = [
            ("get", f"/api/v3/projects/{foreign.id}/quality/"),
            ("post", f"/api/v3/projects/{foreign.id}/quality/score/"),
            ("post", f"/api/v3/projects/{foreign.id}/quality/compliance/"),
            ("post", f"/api/v3/projects/{foreign.id}/quality/accept/"),
            ("post", f"/api/v3/projects/{foreign.id}/quality/revise/"),
        ]
        for method, path in paths:
            if method == "get":
                resp = self.client.get(path)
            elif path.endswith("/accept/"):
                resp = self.client.post(
                    path,
                    {
                        "findings": [
                            {
                                "source": "quality",
                                "finding_key": "defect:0",
                            }
                        ]
                    },
                    format="json",
                )
            else:
                resp = self.client.post(path, {}, format="json")
            self.assertEqual(resp.status_code, 404, msg=path)
