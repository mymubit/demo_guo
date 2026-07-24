# -*- coding: utf-8 -*-
"""独立剧本评审异步评分 / 对比。"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from apps.drama.models import (
    ScriptReview,
    ScriptReviewRun,
    V3ArtifactVersion,
    V3Project,
)
from apps.drama.services import script_review_service as svc
from apps.drama.tests.helpers import SKILLS_ROOT

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_QUALITY = json.loads((_FIXTURES / "v3_quality_report.json").read_text(encoding="utf-8"))
_COMPLIANCE = json.loads(
    (_FIXTURES / "v3_compliance_report.json").read_text(encoding="utf-8")
)

_LLM_CALL_COUNT = {"n": 0}


def _mock_llm_call(prompt: str) -> str:
    _LLM_CALL_COUNT["n"] += 1
    if '"command_type": "score_external_script"' in prompt:
        return json.dumps(_QUALITY, ensure_ascii=False)
    if '"command_type": "check_external_compliance"' in prompt:
        return json.dumps(_COMPLIANCE, ensure_ascii=False)
    raise AssertionError(f"unexpected LLM prompt fragment: {prompt[:200]}")


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    V3_LLM_CALL_OVERRIDE=_mock_llm_call,
)
class V3ScriptReviewAsyncTests(APITestCase):
    def setUp(self) -> None:
        _LLM_CALL_COUNT["n"] = 0
        self.user = get_user_model().objects.create_user(
            username="review_async", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.project = V3Project.objects.create(
            owner=self.user,
            title="关联项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.WRITING,
        )
        self.review = ScriptReview.objects.create(
            owner=self.user,
            project=self.project,
            title="外界评审",
            source_type=ScriptReview.SourceType.PASTE,
            script_text="1-1 场景\n角色A：你好。",
        )

    def test_score_succeeds_without_artifact_write(self) -> None:
        before = V3ArtifactVersion.objects.filter(project=self.project).count()
        resp = self.client.post(f"/api/v3/reviews/{self.review.id}/score/")
        self.assertEqual(resp.status_code, 202, resp.content)
        run_id = resp.json()["data"]["run"]["id"]
        run = ScriptReviewRun.objects.get(id=run_id)
        self.assertEqual(run.status, ScriptReviewRun.Status.SUCCEEDED)
        self.assertEqual(run.report_payload.get("overall_score"), 82)
        self.assertEqual(
            V3ArtifactVersion.objects.filter(project=self.project).count(), before
        )
        self.assertFalse(
            V3ArtifactVersion.objects.filter(
                project=self.project, artifact_key="quality_report"
            ).exists()
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.stage, V3Project.Stage.WRITING)

    def test_score_succeeds_when_llm_omits_resolved_script_key(self) -> None:
        """对齐线上：缺 resolved_script_key 时归一化后仍成功。"""
        incomplete = copy.deepcopy(_QUALITY)
        incomplete.pop("resolved_script_key", None)
        incomplete.pop("scored_artifact", None)

        def _incomplete(prompt: str) -> str:
            if '"command_type": "score_external_script"' in prompt:
                return json.dumps(incomplete, ensure_ascii=False)
            raise AssertionError(prompt[:160])

        with override_settings(V3_LLM_CALL_OVERRIDE=_incomplete):
            resp = self.client.post(f"/api/v3/reviews/{self.review.id}/score/")
        self.assertEqual(resp.status_code, 202, resp.content)
        run = ScriptReviewRun.objects.get(id=resp.json()["data"]["run"]["id"])
        self.assertEqual(run.status, ScriptReviewRun.Status.SUCCEEDED, run.error_message)
        self.assertEqual(run.report_payload.get("resolved_script_key"), "external_script")

    def test_score_succeeds_when_llm_returns_extra_top_level_keys(self) -> None:
        """对齐线上：多吐 external_review_note/total_score 等仍成功。"""
        noisy = copy.deepcopy(_QUALITY)
        noisy.update(
            {
                "external_review_note": "备注",
                "must_fix_issues": [{"title": "必修"}],
                "revision_priority": "节奏",
                "suggested_optimizations": ["钩子"],
                "total_score": 90,
            }
        )

        def _noisy(prompt: str) -> str:
            if '"command_type": "score_external_script"' in prompt:
                return json.dumps(noisy, ensure_ascii=False)
            raise AssertionError(prompt[:160])

        with override_settings(V3_LLM_CALL_OVERRIDE=_noisy):
            resp = self.client.post(f"/api/v3/reviews/{self.review.id}/score/")
        self.assertEqual(resp.status_code, 202, resp.content)
        run = ScriptReviewRun.objects.get(id=resp.json()["data"]["run"]["id"])
        self.assertEqual(run.status, ScriptReviewRun.Status.SUCCEEDED, run.error_message)
        for key in (
            "external_review_note",
            "must_fix_issues",
            "revision_priority",
            "suggested_optimizations",
            "total_score",
        ):
            self.assertNotIn(key, run.report_payload)

    def test_compliance_succeeds(self) -> None:
        resp = self.client.post(f"/api/v3/reviews/{self.review.id}/compliance/")
        self.assertEqual(resp.status_code, 202, resp.content)
        run = ScriptReviewRun.objects.get(id=resp.json()["data"]["run"]["id"])
        self.assertEqual(run.status, ScriptReviewRun.Status.SUCCEEDED)
        self.assertEqual(run.report_payload.get("overall_result"), "通过")

    def test_failed_llm_marks_failed(self) -> None:
        def _bad(_prompt: str) -> str:
            return "not-json"

        with override_settings(V3_LLM_CALL_OVERRIDE=_bad):
            review_run = svc.enqueue_review_run(
                review=self.review, kind=ScriptReviewRun.Kind.QUALITY
            )
            svc.dispatch_review_run(review_run)
            review_run.refresh_from_db()
        self.assertEqual(review_run.status, ScriptReviewRun.Status.FAILED)
        self.assertTrue(review_run.error_message)

    def test_runs_list_and_compare(self) -> None:
        a = ScriptReviewRun.objects.create(
            review=self.review,
            kind=ScriptReviewRun.Kind.QUALITY,
            status=ScriptReviewRun.Status.SUCCEEDED,
            report_payload=copy.deepcopy(_QUALITY),
        )
        right_payload = copy.deepcopy(_QUALITY)
        right_payload["overall_score"] = 86
        b = ScriptReviewRun.objects.create(
            review=self.review,
            kind=ScriptReviewRun.Kind.QUALITY,
            status=ScriptReviewRun.Status.SUCCEEDED,
            report_payload=right_payload,
        )
        ScriptReviewRun.objects.create(
            review=self.review,
            kind=ScriptReviewRun.Kind.COMPLIANCE,
            status=ScriptReviewRun.Status.SUCCEEDED,
            report_payload=copy.deepcopy(_COMPLIANCE),
        )

        list_resp = self.client.get(f"/api/v3/reviews/{self.review.id}/runs/")
        self.assertEqual(list_resp.status_code, 200, list_resp.content)
        self.assertEqual(len(list_resp.json()["data"]["items"]), 3)

        cmp = self.client.get(
            f"/api/v3/reviews/{self.review.id}/compare/",
            {"a": str(a.id), "b": str(b.id)},
        )
        self.assertEqual(cmp.status_code, 200, cmp.content)
        data = cmp.json()["data"]
        self.assertEqual(data["kind"], "quality")
        self.assertEqual(data["deltas"]["overall_score"], 4)

    def test_compare_rejects_different_kind(self) -> None:
        a = ScriptReviewRun.objects.create(
            review=self.review,
            kind=ScriptReviewRun.Kind.QUALITY,
            status=ScriptReviewRun.Status.SUCCEEDED,
            report_payload=copy.deepcopy(_QUALITY),
        )
        b = ScriptReviewRun.objects.create(
            review=self.review,
            kind=ScriptReviewRun.Kind.COMPLIANCE,
            status=ScriptReviewRun.Status.SUCCEEDED,
            report_payload=copy.deepcopy(_COMPLIANCE),
        )
        resp = self.client.get(
            f"/api/v3/reviews/{self.review.id}/compare/",
            {"a": str(a.id), "b": str(b.id)},
        )
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_compare_rejects_failed_run(self) -> None:
        a = ScriptReviewRun.objects.create(
            review=self.review,
            kind=ScriptReviewRun.Kind.QUALITY,
            status=ScriptReviewRun.Status.SUCCEEDED,
            report_payload=copy.deepcopy(_QUALITY),
        )
        b = ScriptReviewRun.objects.create(
            review=self.review,
            kind=ScriptReviewRun.Kind.QUALITY,
            status=ScriptReviewRun.Status.FAILED,
            report_payload={},
        )
        resp = self.client.get(
            f"/api/v3/reviews/{self.review.id}/compare/",
            {"a": str(a.id), "b": str(b.id)},
        )
        self.assertEqual(resp.status_code, 400, resp.content)


class WrapScriptHelperTests(TestCase):
    def test_wrap_script_shape(self) -> None:
        payload = svc.wrap_script_as_episode_scripts(
            title="标题", script_text="对白一行"
        )
        self.assertEqual(payload["episodes"][0]["script"], "对白一行")
        self.assertEqual(payload["episodes"][0]["episode_number"], 1)
