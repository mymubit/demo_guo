# -*- coding: utf-8 -*-
"""P2-W1 Task 1：backup_provider_ids + V3FailoverAttempt 模型。"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.drama.models import (
    DramaLlmProvider,
    V3FailoverAttempt,
    V3Project,
    V3RoleModelMapping,
)


class FailoverModelTests(TestCase):
    def test_mapping_backup_ids_default_empty_and_attempt_create(self) -> None:
        user = get_user_model().objects.create_user("m1", password="x")
        p1 = DramaLlmProvider.objects.create(
            name="A",
            base_url="https://a.example",
            model_name="m",
            api_key_encrypted="x",
            is_enabled=True,
        )
        mapping = V3RoleModelMapping.objects.create(
            role_key="drama-script-writer",
            provider=p1,
        )
        self.assertEqual(mapping.backup_provider_ids, [])
        project = V3Project.objects.create(
            owner=user,
            title="t",
            entry_type="original",
            stage="topic",
        )
        attempt = V3FailoverAttempt.objects.create(
            owner=user,
            v3_project=project,
            role_key="drama-script-writer",
            provider=p1,
            attempt_index=0,
            status=V3FailoverAttempt.Status.SUCCEEDED,
        )
        self.assertEqual(attempt.status, "succeeded")
