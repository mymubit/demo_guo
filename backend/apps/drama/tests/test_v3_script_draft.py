# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.drama.models import V3Project, V3ScriptDraft


class V3ScriptDraftTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="draftu", password="pass12345")
        self.project = V3Project.objects.create(
            owner=self.user,
            title="Script Draft Test",
            entry_type=V3Project.EntryType.ORIGINAL,
        )
        self.sample_payload = {
            "scenes": [
                {
                    "id": "s1",
                    "heading": "INT. 咖啡厅 - 日",
                    "beats": [
                        {"type": "action", "text": "主角推门而入。"},
                        {"type": "dialogue", "text": "好久不见。", "character": "小明"},
                    ],
                }
            ]
        }

    def test_create_script_draft(self) -> None:
        draft = V3ScriptDraft.objects.create(
            project=self.project,
            episode_number=1,
            payload=self.sample_payload,
        )
        self.assertEqual(draft.project_id, self.project.id)
        self.assertEqual(draft.episode_number, 1)
        self.assertEqual(draft.payload["scenes"][0]["heading"], "INT. 咖啡厅 - 日")
        self.assertEqual(len(draft.payload["scenes"][0]["beats"]), 2)
        self.assertIsNotNone(draft.updated_at)

    def test_unique_project_episode(self) -> None:
        V3ScriptDraft.objects.create(
            project=self.project,
            episode_number=2,
            payload=self.sample_payload,
        )
        with self.assertRaises(IntegrityError):
            V3ScriptDraft.objects.create(
                project=self.project,
                episode_number=2,
                payload={"scenes": []},
            )

    def test_update_or_create_overwrites_payload(self) -> None:
        V3ScriptDraft.objects.create(
            project=self.project,
            episode_number=3,
            payload={"scenes": []},
        )
        draft, created = V3ScriptDraft.objects.update_or_create(
            project=self.project,
            episode_number=3,
            defaults={"payload": self.sample_payload},
        )
        self.assertFalse(created)
        self.assertEqual(draft.payload["scenes"][0]["id"], "s1")

    def test_different_episodes_same_project_allowed(self) -> None:
        V3ScriptDraft.objects.create(
            project=self.project,
            episode_number=1,
            payload=self.sample_payload,
        )
        draft2 = V3ScriptDraft.objects.create(
            project=self.project,
            episode_number=2,
            payload={"scenes": []},
        )
        self.assertEqual(draft2.episode_number, 2)
        self.assertEqual(V3ScriptDraft.objects.filter(project=self.project).count(), 2)
