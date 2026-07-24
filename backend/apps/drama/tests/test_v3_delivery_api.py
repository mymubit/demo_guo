# -*- coding: utf-8 -*-
"""V3 W4：Delivery REST API（eager + mock LLM）。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.models import V3ArtifactVersion, V3Project
from apps.drama.orchestrator.report_meta import attach_script_meta
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
_QUALITY = json.loads(
    (_FIXTURE_DIR / "v3_quality_report.json").read_text(encoding="utf-8")
)
_COMPLIANCE = json.loads(
    (_FIXTURE_DIR / "v3_compliance_report.json").read_text(encoding="utf-8")
)
_PACKAGE = json.loads(
    (_FIXTURE_DIR / "v3_production_package.json").read_text(encoding="utf-8")
)
_BLUEPRINT_KEYS = recipe_for("generate_blueprint")["writes"]


def _mock_llm_call(prompt: str) -> str:
    if '"command_type": "prepare_delivery"' in prompt:
        return json.dumps(_PACKAGE, ensure_ascii=False)
    raise AssertionError(f"unexpected LLM prompt fragment: {prompt[:160]}")


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    V3_LLM_CALL_OVERRIDE=_mock_llm_call,
)
class V3DeliveryApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="delivery_api", password="pass12345"
        )
        self.other = user_model.objects.create_user(
            username="delivery_other", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.project = V3Project.objects.create(
            owner=self.user,
            title="交付 API 项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.QUALITY,
        )
        self.base = f"/api/v3/projects/{self.project.id}/delivery"

    def _commit(self, key: str, payload: dict, *, version: int = 1) -> V3ArtifactVersion:
        return V3ArtifactVersion.objects.create(
            project=self.project,
            artifact_key=key,
            version=version,
            status=V3ArtifactVersion.Status.COMMITTED,
            payload=payload,
        )

    def _seed_writing_deps(self) -> V3ArtifactVersion:
        self._commit("project_brief", _BRIEF)
        for key in _BLUEPRINT_KEYS:
            self._commit(key, _BLUEPRINT[key])
        self._commit("episode_plan", _EPISODE_PLAN)
        return self._commit("episode_scripts", copy.deepcopy(_SCRIPTS))

    def _seed_passing_reports(self, scripts: V3ArtifactVersion) -> None:
        self._commit(
            "quality_report",
            attach_script_meta(copy.deepcopy(_QUALITY), script_art=scripts),
        )
        self._commit(
            "compliance_report",
            attach_script_meta(copy.deepcopy(_COMPLIANCE), script_art=scripts),
        )

    def test_get_empty_delivery_state_gate_blocked(self) -> None:
        resp = self.client.get(f"{self.base}/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(data["stage"], "quality")
        self.assertFalse(data["gate"]["passed"])
        self.assertTrue(data["gate"]["blockers"])
        self.assertIn("正文", data["gate"]["blockers"][0])
        self.assertIsNone(data["package"])
        self.assertIsNone(data["latest_run"])

    def test_get_gate_passed_with_package(self) -> None:
        scripts = self._seed_writing_deps()
        self._seed_passing_reports(scripts)
        package = self._commit("production_package", copy.deepcopy(_PACKAGE))
        self.project.stage = V3Project.Stage.DELIVERY
        self.project.save(update_fields=["stage", "updated_at"])

        resp = self.client.get(f"{self.base}/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["stage"], "delivery")
        self.assertTrue(data["gate"]["passed"])
        self.assertEqual(data["gate"]["blockers"], [])
        self.assertEqual(data["package"]["id"], str(package.id))
        self.assertEqual(data["package"]["artifact_key"], "production_package")
        self.assertEqual(data["package"]["status"], "committed")
        self.assertIsNone(data["latest_run"])

    def test_prepare_gate_fail_returns_200_failed_run(self) -> None:
        """门禁失败：HTTP 200 + command_run.status=failed，中文 blockers。"""
        self._seed_writing_deps()
        resp = self.client.post(f"{self.base}/prepare/", {}, format="json")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        run = body["data"]["command_run"]
        self.assertEqual(run["command_type"], "prepare_delivery")
        self.assertEqual(run["status"], "failed")
        self.assertTrue(run["error_message"])
        self.assertIn("质量报告", run["error_message"])
        self.assertNotIn("Traceback", run["error_message"])

        state = self.client.get(f"{self.base}/").json()["data"]
        self.assertEqual(state["latest_run"]["id"], run["id"])
        self.assertIsNone(state["package"])

    def test_prepare_success_commits_package_and_stage(self) -> None:
        scripts = self._seed_writing_deps()
        self._seed_passing_reports(scripts)

        resp = self.client.post(f"{self.base}/prepare/", {}, format="json")
        self.assertEqual(resp.status_code, 200)
        run = resp.json()["data"]["command_run"]
        self.assertEqual(run["command_type"], "prepare_delivery")
        self.assertEqual(run["status"], "succeeded")
        self.assertNotIn("Traceback", run.get("error_message") or "")

        self.project.refresh_from_db()
        self.assertEqual(self.project.stage, V3Project.Stage.DELIVERY)

        state = self.client.get(f"{self.base}/").json()["data"]
        self.assertEqual(state["stage"], "delivery")
        self.assertTrue(state["gate"]["passed"])
        self.assertIsNotNone(state["package"])
        self.assertEqual(state["package"]["status"], "committed")
        self.assertEqual(state["package"]["artifact_key"], "production_package")
        self.assertEqual(state["latest_run"]["id"], run["id"])

    def test_owner_isolation_returns_404(self) -> None:
        foreign = V3Project.objects.create(
            owner=self.other,
            title="他人交付",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        paths = [
            ("get", f"/api/v3/projects/{foreign.id}/delivery/"),
            ("post", f"/api/v3/projects/{foreign.id}/delivery/prepare/"),
        ]
        for method, path in paths:
            if method == "get":
                resp = self.client.get(path)
            else:
                resp = self.client.post(path, {}, format="json")
            self.assertEqual(resp.status_code, 404, msg=path)
