# -*- coding: utf-8 -*-
"""????M4-M6???????????

????
  ??CreationFeedback ??????
  ??UserBehaviorEvent ??
  ?????????content_quality_summary / funnel / stuck??
  ????????
  ??????????
  ??Dashboard ??
"""
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.creation.models import Project
from apps.creation.services.content_quality import (
    content_quality_funnel,
    content_quality_summary,
    detect_and_mark_abandoned,
    record_final_export,
    record_user_edit,
    stuck_projects,
)
from apps.operations.models import CreationFeedback, UserBehaviorEvent
from apps.operations.services import feedback_summary, track_event

User = get_user_model()


class CreationFeedbackTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13800001001", password="x")
        self.project = Project.objects.create(
            user=self.user,
            title="??????",
            theme="sweet-pet",
            episode_count=20,
            pipeline_mode=Project.MODE_WORKSPACE,
            creation_entry="from-scratch",
        )

    def test_create_and_query_feedback(self):
        feedback = CreationFeedback.objects.create(
            user=self.user,
            project=self.project,
            category=CreationFeedback.Category.BUG,
            severity=CreationFeedback.Severity.P1,
            title="??????",
            content="????3 ?????? 2s",
        )
        self.assertEqual(feedback.status, CreationFeedback.Status.OPEN)
        self.assertEqual(feedback.severity, "P1")
        self.assertIn("??????", feedback.title)

    def test_default_severity(self):
        fb = CreationFeedback.objects.create(
            user=self.user, title="????", content="",
        )
        self.assertEqual(fb.severity, "P2")
        self.assertEqual(fb.source, CreationFeedback.Source.WORKSPACE)


class UserBehaviorEventTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13800001002", password="x")

    def test_track_event_persists(self):
        ok = track_event(
            event_name="creation_submitted",
            user=self.user,
            project_id="11111111-1111-1111-1111-111111111111",
            page="/api/creation/submit",
            payload={"theme": "x", "episode_count": 30},
        )
        self.assertTrue(ok)
        evt = UserBehaviorEvent.objects.get(event_name="creation_submitted")
        self.assertEqual(evt.user_id, self.user.id)
        self.assertEqual(evt.project_id, "11111111-1111-1111-1111-111111111111")
        self.assertEqual(evt.source, "backend")

    def test_track_event_invalid_name(self):
        ok = track_event(event_name="not_a_real_event", user=self.user)
        self.assertFalse(ok)
        self.assertEqual(UserBehaviorEvent.objects.count(), 0)

    def test_track_event_anonymous(self):
        ok = track_event(
            event_name="landing_view",
            user=None,
            session_id="s_xxx",
            payload={"referrer": "google"},
            source="frontend",
        )
        self.assertTrue(ok)
        evt = UserBehaviorEvent.objects.get(event_name="landing_view")
        self.assertIsNone(evt.user_id)
        self.assertEqual(evt.session_id, "s_xxx")


class ContentQualityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13800001003", password="x")
        now = timezone.now()
        from apps.drama.constants import DramaStage
        from apps.drama.models import DramaRoleExecution

        self.p1 = Project.objects.create(
            user=self.user, title="p1", theme="t1", episode_count=10,
            pipeline_mode=Project.MODE_WORKSPACE,
            creation_entry="from-scratch", user_edit_count=5, final_export_count=2,
            track_mode="fast",
            delivery_status="delivered",
            drama_stage=DramaStage.DELIVERED,
            core_idea="p1",
            created_at=now - timedelta(days=2),
        )
        self.p2 = Project.objects.create(
            user=self.user, title="p2", theme="t2", episode_count=8,
            pipeline_mode=Project.MODE_WORKSPACE,
            creation_entry="from-outline", user_edit_count=3, final_export_count=0,
            track_mode="fast",
            drama_stage=DramaStage.WRITING,
            core_idea="p2",
            created_at=now - timedelta(days=1),
        )
        self.p3 = Project.objects.create(
            user=self.user, title="p3", theme="t3", episode_count=5,
            pipeline_mode=Project.MODE_WORKSPACE,
            creation_entry="from-scratch", user_edit_count=0, final_export_count=0,
            track_mode="fast",
            drama_stage=DramaStage.WRITING,
            core_idea="p3",
            abandoned_at=now - timedelta(days=1), created_at=now - timedelta(days=3),
        )
        DramaRoleExecution.objects.create(
            project=self.p3,
            agent_id="drama.topic-planner",
            agent_name_zh="?????",
            status=DramaRoleExecution.Status.FAILED,
            error_message="????",
        )

    def test_content_quality_summary(self):
        s = content_quality_summary(days=30)
        self.assertEqual(s["total_projects"], 3)
        self.assertEqual(s["exported_count"], 1)  # p1
        self.assertEqual(s["edited_count"], 2)  # p1 + p2
        self.assertEqual(s["abandoned_count"], 1)  # p3
        self.assertEqual(s["completed_count"], 1)  # p1
        self.assertGreater(s["save_rate"], 0)
        self.assertGreater(s["export_rate"], 0)

    def test_content_quality_funnel(self):
        f = content_quality_funnel(days=30)
        self.assertEqual(f["submitted"], 3)
        self.assertEqual(f["saved"], 2)
        self.assertEqual(f["completed"], 1)
        self.assertEqual(f["exported"], 1)
        self.assertEqual(f["abandoned"], 1)
        # 4 ??stage
        self.assertEqual(len(f["stages"]), 4)

    def test_record_user_edit_clears_abandoned(self):
        self.p3.user_edit_count = 0
        self.p3.abandoned_at = timezone.now() - timedelta(days=1)
        self.p3.save()
        record_user_edit(self.p3)
        self.p3.refresh_from_db()
        self.assertEqual(self.p3.user_edit_count, 1)
        self.assertIsNone(self.p3.abandoned_at)
        self.assertIsNotNone(self.p3.last_edited_at)

    def test_record_final_export_increments(self):
        record_final_export(self.p1)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.final_export_count, 3)

    def test_detect_and_mark_abandoned_marks_7d_old(self):
        from apps.drama.constants import DramaStage

        old = Project.objects.create(
            user=self.user, title="old", theme="t", episode_count=5,
            pipeline_mode=Project.MODE_WORKSPACE,
            creation_entry="from-scratch",
            track_mode="fast",
            drama_stage=DramaStage.WRITING,
            core_idea="old",
            created_at=timezone.now() - timedelta(days=20),
        )
        count = detect_and_mark_abandoned(days=7)
        self.assertGreaterEqual(count, 1)
        old.refresh_from_db()
        self.assertIsNotNone(old.abandoned_at)

    def test_stuck_projects(self):
        stuck = stuck_projects(days=3, limit=10)
        # p2 ??STATUS_RUNNING + ??????3 ????????
        # p3 ??STATUS_FAILED??????
        # ????????p1 ????p3 ????
        self.assertIsInstance(stuck, list)


class FeedbackSummaryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13800001004", password="x")
        # ????/?????????
        for i in range(3):
            CreationFeedback.objects.create(
                user=self.user, title=f"bug {i}", content="x",
                category=CreationFeedback.Category.BUG,
                severity=CreationFeedback.Severity.P0 if i == 0 else CreationFeedback.Severity.P2,
                status=CreationFeedback.Status.OPEN,
            )
        CreationFeedback.objects.create(
            user=self.user, title="feature", content="x",
            category=CreationFeedback.Category.FEATURE_REQUEST,
            severity=CreationFeedback.Severity.P3,
            status=CreationFeedback.Status.RESOLVED,
        )

    def test_feedback_summary(self):
        summary = feedback_summary(days=30)
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["open"], 3)
        self.assertEqual(summary["resolved"], 1)
        self.assertEqual(summary["p0_open"], 1)
        self.assertEqual(len(summary["by_category"]), 2)
        self.assertEqual(len(summary["by_severity"]), 3)
