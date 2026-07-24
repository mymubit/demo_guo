# -*- coding: utf-8 -*-
"""V3 W2 Task 8：幂等键去重（同 owner+key 不双建项目/双候选）。"""
from __future__ import annotations

import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3Project
from apps.drama.orchestrator import dispatch_command
from apps.drama.tests.helpers import SKILLS_ROOT

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
_BRIEF_PAYLOAD = json.loads(
    (_FIXTURE_DIR / "v3_project_brief_candidate.json").read_text(encoding="utf-8")
)


def _mock_llm_call(prompt: str) -> str:
    return json.dumps(_BRIEF_PAYLOAD, ensure_ascii=False)


@override_settings(
    DRAMA_SKILLS_ROOT=SKILLS_ROOT,
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    V3_LLM_CALL_OVERRIDE=_mock_llm_call,
)
class V3IdempotencyTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="idem_w2", password="pass12345"
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="幂等测试项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.TOPIC,
        )

    def test_create_project_same_idempotency_key_does_not_duplicate(self) -> None:
        payload = {"title": "幂等新剧", "entry_type": "original"}
        key = "create-project-once"

        first = dispatch_command(
            owner=self.user,
            command_type="create_project",
            payload=payload,
            idempotency_key=key,
        )
        second = dispatch_command(
            owner=self.user,
            command_type="create_project",
            payload=payload,
            idempotency_key=key,
        )

        self.assertEqual(first.id, second.id)
        self.assertEqual(V3CommandRun.objects.filter(owner=self.user, idempotency_key=key).count(), 1)
        self.assertEqual(V3Project.objects.filter(owner=self.user, title="幂等新剧").count(), 1)

    def test_generate_topic_brief_same_idempotency_key_does_not_duplicate(self) -> None:
        key = "generate-brief-once"
        payload = {"project_id": str(self.project.id)}

        first = dispatch_command(
            owner=self.user,
            command_type="generate_topic_brief",
            payload=payload,
            idempotency_key=key,
        )
        second = dispatch_command(
            owner=self.user,
            command_type="generate_topic_brief",
            payload=payload,
            idempotency_key=key,
        )

        first.refresh_from_db()
        self.assertEqual(first.status, V3CommandRun.Status.SUCCEEDED)
        self.assertEqual(first.id, second.id)
        self.assertEqual(V3CommandRun.objects.filter(owner=self.user, idempotency_key=key).count(), 1)
        self.assertEqual(
            V3ArtifactVersion.objects.filter(
                project=self.project,
                artifact_key="project_brief",
                status=V3ArtifactVersion.Status.CANDIDATE,
            ).count(),
            1,
        )

    def test_failed_run_allows_retry_with_same_idempotency_key(self) -> None:
        key = "retry-after-fail"
        V3CommandRun.objects.create(
            owner=self.user,
            command_type="create_project",
            status=V3CommandRun.Status.FAILED,
            idempotency_key=key,
            request_payload={"title": "", "entry_type": "original"},
            error_message="标题与创作来源（原创/改编）不能为空",
        )

        run = dispatch_command(
            owner=self.user,
            command_type="create_project",
            payload={"title": "重试成功", "entry_type": "original"},
            idempotency_key=key,
        )

        self.assertEqual(run.status, V3CommandRun.Status.SUCCEEDED)
        self.assertEqual(V3CommandRun.objects.filter(owner=self.user, idempotency_key=key).count(), 2)

    def test_empty_idempotency_key_always_creates_new_run(self) -> None:
        payload = {"title": "无键项目", "entry_type": "adapt"}

        first = dispatch_command(
            owner=self.user,
            command_type="create_project",
            payload=payload,
            idempotency_key="",
        )
        second = dispatch_command(
            owner=self.user,
            command_type="create_project",
            payload=payload,
            idempotency_key="",
        )

        self.assertNotEqual(first.id, second.id)
        self.assertEqual(V3Project.objects.filter(owner=self.user, title="无键项目").count(), 2)

    def test_same_idempotency_key_different_command_type_not_reused(self) -> None:
        """幂等查找绑定 (owner, key, command_type)，不同命令不互相复用。"""
        key = "shared-across-commands"
        create_run = dispatch_command(
            owner=self.user,
            command_type="create_project",
            payload={"title": "键共享项目", "entry_type": "original"},
            idempotency_key=key,
        )
        self.assertEqual(create_run.status, V3CommandRun.Status.SUCCEEDED)

        gen_run = dispatch_command(
            owner=self.user,
            command_type="generate_topic_brief",
            payload={"project_id": str(self.project.id)},
            idempotency_key=key,
        )
        gen_run.refresh_from_db()
        self.assertNotEqual(create_run.id, gen_run.id)
        self.assertEqual(gen_run.status, V3CommandRun.Status.SUCCEEDED)
        self.assertEqual(gen_run.command_type, "generate_topic_brief")
        self.assertEqual(
            V3CommandRun.objects.filter(owner=self.user, idempotency_key=key).count(),
            2,
        )
