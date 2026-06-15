# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.creation.orchestration.polish_apply import apply_polish_suggestions
from apps.creation.artifact_service import get_artifact, save_artifact
from apps.creation.models import Project

User = get_user_model()


class PolishApplyIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13900004405", password="test-pass-123")
        self.project = Project.objects.create(
            user=self.user,
            title="润色应用测试",
            theme="sweet-pet",
            episode_count=2,
        )
        save_artifact(
            self.project,
            "episode_scripts",
            {
                "episodes": [
                    {"episodeNumber": 1, "title": "第1集", "full_script_text": "对白"},
                    {"episodeNumber": 2, "title": "第2集", "full_script_text": "对白2"},
                ]
            },
        )
        save_artifact(
            self.project,
            "polish_log",
            {
                "suggestions": [
                    {"episodeNumber": 1, "field": "dialogue", "advice": "缩短开场对白"},
                    {"episodeNumber": 2, "field": "pacing", "advice": "加快节奏"},
                ]
            },
        )

    def test_apply_polish_writes_revision_notes(self):
        out = apply_polish_suggestions(self.project, indices=[0, 1])
        self.assertEqual(out["appliedCount"], 2)
        scripts = get_artifact(self.project, "episode_scripts") or {}
        ep1 = (scripts.get("episodes") or [])[0]
        notes = ep1.get("polishRevisionNotes") or []
        self.assertEqual(len(notes), 1)
        self.assertIn("缩短", notes[0]["advice"])

    def test_apply_all_marks_polish_log(self):
        apply_polish_suggestions(self.project, apply_all=True)
        polish = get_artifact(self.project, "polish_log") or {}
        self.assertTrue(polish.get("applied"))
        self.assertIn(0, polish.get("appliedIndices") or [])
