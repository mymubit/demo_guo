# -*- coding: utf-8 -*-
"""W5 Task 6：V3 LLM 日志挂 run + Logs REST。"""
from __future__ import annotations

import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.drama.models import (
    DramaLlmCallLog,
    DramaLlmProvider,
    V3CommandRun,
    V3FailoverAttempt,
    V3Project,
)
from apps.drama.services.llm_call_log_service import LlmCallLogService
from apps.drama.services.secret_crypto import encrypt_secret
from apps.drama.skills_bridge.executor import execute_generation
from apps.drama.tests.helpers import SKILLS_ROOT

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
_BRIEF_PAYLOAD = json.loads(
    (_FIXTURE_DIR / "v3_project_brief_candidate.json").read_text(encoding="utf-8")
)


def _mock_llm_that_records(prompt: str) -> str:
    """模拟生成并走 LlmCallLogService.record（依赖 executor 注入的 llm_call_scope）。"""
    body = json.dumps(_BRIEF_PAYLOAD, ensure_ascii=False)
    LlmCallLogService.record(
        system_prompt="你是短剧创作助手，只输出合法 JSON。",
        user_prompt=prompt,
        model_name="mock-model",
        base_url="https://llm.example/v1",
        status=DramaLlmCallLog.Status.SUCCESS,
        latency_ms=12,
        response_text=body,
        response_json={
            "choices": [{"message": {"content": body}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        },
    )
    return body


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class V3LogsApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="logs_owner", password="pass12345"
        )
        self.other = user_model.objects.create_user(
            username="logs_other", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.project = V3Project.objects.create(
            owner=self.user,
            title="日志项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.TOPIC,
        )
        self.other_project = V3Project.objects.create(
            owner=self.other,
            title="他人项目",
            entry_type=V3Project.EntryType.ORIGINAL,
            stage=V3Project.Stage.TOPIC,
        )

    def test_generate_links_llm_call_to_v3_run(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.RUNNING,
            request_payload={},
        )
        execute_generation(
            command_type="generate_topic_brief",
            project=self.project,
            run=run,
            llm_call=_mock_llm_that_records,
        )
        log = DramaLlmCallLog.objects.latest("created_at")
        self.assertEqual(str(log.v3_command_run_id), str(run.id))
        self.assertEqual(str(log.v3_project_id), str(self.project.id))
        self.assertIn(_BRIEF_PAYLOAD["title"], log.response_text)

    def test_list_runs_owner_scoped_and_filters(self) -> None:
        mine = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.SUCCEEDED,
        )
        V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_blueprint",
            status=V3CommandRun.Status.FAILED,
        )
        V3CommandRun.objects.create(
            owner=self.other,
            project=self.other_project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.SUCCEEDED,
        )

        resp = self.client.get("/api/v3/logs/runs/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertIn("items", data)
        self.assertLessEqual(data.get("limit", 20), 50)
        ids = {item["id"] for item in data["items"]}
        self.assertIn(str(mine.id), ids)
        self.assertEqual(len(data["items"]), 2)

        filtered = self.client.get(
            "/api/v3/logs/runs/",
            {
                "project_id": str(self.project.id),
                "status": "succeeded",
                "command_type": "generate_topic_brief",
            },
        )
        self.assertEqual(filtered.status_code, 200)
        items = filtered.json()["data"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], str(mine.id))

    def test_list_runs_limit_capped_at_50(self) -> None:
        resp = self.client.get("/api/v3/logs/runs/", {"limit": 999})
        self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(resp.json()["data"]["limit"], 50)

    def test_run_detail_includes_truncated_calls(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.SUCCEEDED,
        )
        execute_generation(
            command_type="generate_topic_brief",
            project=self.project,
            run=run,
            llm_call=_mock_llm_that_records,
        )
        log = DramaLlmCallLog.objects.filter(v3_command_run=run).latest("created_at")

        resp = self.client.get(f"/api/v3/logs/runs/{run.id}/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["id"], str(run.id))
        self.assertEqual(data["command_type"], "generate_topic_brief")
        self.assertIn("calls", data)
        self.assertEqual(len(data["calls"]), 1)
        call = data["calls"][0]
        self.assertEqual(call["id"], str(log.id))
        self.assertEqual(call["v3_command_run_id"], str(run.id))
        self.assertNotIn("api_key", json.dumps(call))
        # 详情可截断：至少有正文或 preview
        self.assertTrue(
            call.get("system_prompt")
            or call.get("system_prompt_preview")
            or call.get("user_prompt")
            or call.get("user_prompt_preview")
        )

    def test_call_detail_full_snapshot_no_api_key(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.SUCCEEDED,
        )
        execute_generation(
            command_type="generate_topic_brief",
            project=self.project,
            run=run,
            llm_call=_mock_llm_that_records,
        )
        log = DramaLlmCallLog.objects.filter(v3_command_run=run).latest("created_at")

        resp = self.client.get(f"/api/v3/logs/calls/{log.id}/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["id"], str(log.id))
        self.assertEqual(data["system_prompt"], log.system_prompt)
        self.assertEqual(data["user_prompt"], log.user_prompt)
        self.assertEqual(data["response_text"], log.response_text)
        self.assertEqual(data["v3_command_run_id"], str(run.id))
        self.assertEqual(data["v3_project_id"], str(self.project.id))
        blob = json.dumps(data)
        self.assertNotIn("api_key", blob)
        self.assertNotIn("sk-", blob)

    def test_other_owner_run_and_call_404(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.other,
            project=self.other_project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.SUCCEEDED,
        )
        log = DramaLlmCallLog.objects.create(
            v3_command_run=run,
            v3_project=self.other_project,
            role="drama.topic-director",
            purpose=DramaLlmCallLog.Purpose.ARTIFACT_GENERATION,
            status=DramaLlmCallLog.Status.SUCCESS,
            model_name="x",
            system_prompt="s",
            user_prompt="u",
            response_text="{}",
        )
        run_resp = self.client.get(f"/api/v3/logs/runs/{run.id}/")
        self.assertEqual(run_resp.status_code, 404)
        call_resp = self.client.get(f"/api/v3/logs/calls/{log.id}/")
        self.assertEqual(call_resp.status_code, 404)

    def test_run_detail_includes_failover_attempts(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic_brief",
            status=V3CommandRun.Status.SUCCEEDED,
        )
        primary = DramaLlmProvider.objects.create(
            name="主供应商",
            base_url="https://primary.example/v1",
            model_name="gpt-primary",
            api_key_encrypted=encrypt_secret("sk-primary"),
            is_enabled=True,
            is_active=True,
        )
        backup = DramaLlmProvider.objects.create(
            name="备选供应商",
            base_url="https://backup.example/v1",
            model_name="gpt-backup",
            api_key_encrypted=encrypt_secret("sk-backup"),
            is_enabled=True,
            is_active=False,
        )
        a0 = V3FailoverAttempt.objects.create(
            v3_command_run=run,
            v3_project=self.project,
            owner=self.user,
            role_key="drama-topic-director",
            provider=primary,
            attempt_index=0,
            status=V3FailoverAttempt.Status.FAILED_SWITCHABLE,
            error_code="http_503",
            error_message="LLM HTTP 503: unavailable",
        )
        a1 = V3FailoverAttempt.objects.create(
            v3_command_run=run,
            v3_project=self.project,
            owner=self.user,
            role_key="drama-topic-director",
            provider=backup,
            attempt_index=1,
            status=V3FailoverAttempt.Status.SUCCEEDED,
        )

        resp = self.client.get(f"/api/v3/logs/runs/{run.id}/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertIn("failover_attempts", data)
        attempts = data["failover_attempts"]
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]["id"], str(a0.id))
        self.assertEqual(attempts[0]["attempt_index"], 0)
        self.assertEqual(attempts[0]["provider_id"], str(primary.id))
        self.assertEqual(attempts[0]["provider_name"], "主供应商")
        self.assertEqual(attempts[0]["status"], "failed_switchable")
        self.assertEqual(attempts[0]["error_code"], "http_503")
        self.assertEqual(attempts[0]["error_message"], "LLM HTTP 503: unavailable")
        self.assertIsNone(attempts[0]["llm_call_log_id"])
        self.assertIn("created_at", attempts[0])
        self.assertEqual(attempts[1]["id"], str(a1.id))
        self.assertEqual(attempts[1]["attempt_index"], 1)
        self.assertEqual(attempts[1]["provider_name"], "备选供应商")
        self.assertEqual(attempts[1]["status"], "succeeded")
        # 按 attempt_index 升序
        self.assertEqual(
            [item["attempt_index"] for item in attempts],
            [0, 1],
        )
