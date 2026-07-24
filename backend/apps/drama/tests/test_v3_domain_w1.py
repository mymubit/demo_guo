# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.drama.models import V3CommandRun, V3Project


class V3DomainW1Tests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="w1u", password="pass12345")

    def test_project_can_be_archived(self) -> None:
        p = V3Project.objects.create(
            owner=self.user, title="A", entry_type="original"
        )
        self.assertIsNone(p.archived_at)
        p.archived_at = timezone.now()
        p.save(update_fields=["archived_at", "updated_at"])
        p.refresh_from_db()
        self.assertIsNotNone(p.archived_at)

    def test_command_run_defaults(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            command_type="create_project",
            status=V3CommandRun.Status.SUCCEEDED,
            request_payload={"title": "A", "entry_type": "original"},
            result_payload={},
        )
        self.assertEqual(run.command_type, "create_project")
        self.assertIsNone(run.project)
