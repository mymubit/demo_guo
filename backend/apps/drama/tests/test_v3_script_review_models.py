# -*- coding: utf-8 -*-
"""ScriptReview 模型冒烟。"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.drama.models import ScriptReview, ScriptReviewRun, V3Project


class ScriptReviewModelTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="review_model", password="pass12345"
        )

    def test_create_review_without_project(self) -> None:
        review = ScriptReview.objects.create(
            owner=self.user,
            title="外界稿",
            source_type=ScriptReview.SourceType.PASTE,
            script_text="第一场\n对白。",
        )
        self.assertIsNone(review.project_id)
        self.assertEqual(review.source_type, "paste")

    def test_create_review_with_project(self) -> None:
        project = V3Project.objects.create(
            owner=self.user,
            title="关联项目",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        review = ScriptReview.objects.create(
            owner=self.user,
            project=project,
            title="关联稿",
            source_type=ScriptReview.SourceType.UPLOAD,
            source_filename="a.txt",
            script_text="正文",
        )
        self.assertEqual(review.project_id, project.id)

    def test_create_run_history(self) -> None:
        review = ScriptReview.objects.create(
            owner=self.user,
            title="历史",
            source_type=ScriptReview.SourceType.PASTE,
            script_text="正文",
        )
        run = ScriptReviewRun.objects.create(
            review=review,
            kind=ScriptReviewRun.Kind.QUALITY,
            status=ScriptReviewRun.Status.SUCCEEDED,
            report_payload={"overall_score": 80},
        )
        self.assertEqual(review.runs.count(), 1)
        self.assertEqual(run.report_payload["overall_score"], 80)

    def test_project_null_on_project_delete(self) -> None:
        project = V3Project.objects.create(
            owner=self.user,
            title="将删",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        review = ScriptReview.objects.create(
            owner=self.user,
            project=project,
            title="仍在",
            source_type=ScriptReview.SourceType.PASTE,
            script_text="正文",
        )
        project.delete()
        review.refresh_from_db()
        self.assertIsNone(review.project_id)

    def test_cascade_delete_runs(self) -> None:
        review = ScriptReview.objects.create(
            owner=self.user,
            title="级联",
            source_type=ScriptReview.SourceType.PASTE,
            script_text="正文",
        )
        ScriptReviewRun.objects.create(
            review=review,
            kind=ScriptReviewRun.Kind.COMPLIANCE,
        )
        review_id = review.id
        review.delete()
        self.assertFalse(ScriptReviewRun.objects.filter(review_id=review_id).exists())
