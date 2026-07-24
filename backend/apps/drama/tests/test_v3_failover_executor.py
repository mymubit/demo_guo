# -*- coding: utf-8 -*-
"""P2-W1 Task 4：executor 经 llm_router 故障转移；试连不写 FailoverAttempt。"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.drama.models import (
    DramaLlmProvider,
    V3ArtifactVersion,
    V3CommandRun,
    V3FailoverAttempt,
    V3Project,
    V3RoleModelMapping,
)
from apps.drama.orchestrator import dispatch_command
from apps.drama.services.llm_provider import LlmProviderError
from apps.drama.services.secret_crypto import encrypt_secret
from apps.drama.skills_bridge.executor import execute_generation
from apps.drama.tests.helpers import SKILLS_ROOT

_BRIEF_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "v3_project_brief_candidate.json"
)


def _make_provider(**overrides) -> DramaLlmProvider:
    data = {
        "name": "provider",
        "base_url": "https://llm.example/v1",
        "model_name": "gpt-test",
        "api_key_encrypted": encrypt_secret("sk-test"),
        "temperature": 0.7,
        "max_tokens": 4096,
        "is_enabled": True,
        "is_active": False,
    }
    data.update(overrides)
    return DramaLlmProvider.objects.create(**data)


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class FailoverExecutorTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="failover-exec", password="x"
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="Failover 选题",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage="topic",
        )
        self.brief_payload = json.loads(_BRIEF_FIXTURE.read_text(encoding="utf-8"))

    @patch("apps.drama.services.llm_provider.LlmProvider.chat_completion")
    def test_execute_generation_failovers_and_writes_attempts(
        self, mock_chat
    ) -> None:
        p1 = _make_provider(name="Primary", is_active=True)
        p2 = _make_provider(
            name="Backup",
            base_url="https://backup.example/v1",
            model_name="gpt-backup",
        )
        V3RoleModelMapping.objects.create(
            role_key="drama-topic-director",
            provider=p1,
            backup_provider_ids=[str(p2.id)],
        )
        content = json.dumps(self.brief_payload, ensure_ascii=False)
        calls: list[str] = []

        def chat_side_effect(*, config=None, **_kwargs):
            base = config.base_url if config else ""
            calls.append(base)
            if len(calls) == 1:
                raise LlmProviderError("LLM HTTP 503: unavailable")
            return {"choices": [{"message": {"content": content}}]}

        mock_chat.side_effect = chat_side_effect

        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.RUNNING,
        )
        created = execute_generation(
            command_type="generate_topic_brief",
            project=self.project,
            run=run,
        )

        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].artifact_key, "project_brief")
        self.assertEqual(created[0].status, V3ArtifactVersion.Status.CANDIDATE)
        self.assertEqual(created[0].payload["title"], self.brief_payload["title"])
        self.assertEqual(len(calls), 2)

        attempts = list(V3FailoverAttempt.objects.order_by("attempt_index"))
        self.assertGreaterEqual(len(attempts), 2)
        self.assertEqual(
            [a.status for a in attempts[:2]],
            [
                V3FailoverAttempt.Status.FAILED_SWITCHABLE,
                V3FailoverAttempt.Status.SUCCEEDED,
            ],
        )
        self.assertEqual(attempts[0].provider_id, p1.id)
        self.assertEqual(attempts[1].provider_id, p2.id)
        self.assertEqual(attempts[0].v3_command_run_id, run.id)
        self.assertEqual(attempts[0].v3_project_id, self.project.id)

    @patch("apps.drama.orchestrator.provider_test.requests.get")
    def test_connectivity_does_not_create_failover_attempts(self, mock_get) -> None:
        provider = _make_provider(name="ProbeOnly", is_active=True)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"data":[]}'
        mock_get.return_value = mock_resp

        run = dispatch_command(
            owner=self.user,
            command_type="test_model_provider",
            payload={"provider_id": str(provider.id)},
        )
        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        self.assertEqual(V3FailoverAttempt.objects.count(), 0)
        mock_get.assert_called_once()
