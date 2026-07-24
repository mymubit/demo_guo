# -*- coding: utf-8 -*-
"""P2-W2 Task 4：Usage summary API。"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone as dj_timezone
from rest_framework.test import APITestCase

from apps.drama.models import (
    DramaLlmCallLog,
    DramaLlmProvider,
    V3CommandRun,
    V3ModelPrice,
    V3Project,
    V3UsageDailyRollup,
)

_SUMMARY = "/api/v3/usage/summary/"


class V3UsageSummaryApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="usage_owner", password="pass12345"
        )
        self.other = user_model.objects.create_user(
            username="usage_other", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.provider = DramaLlmProvider.objects.create(
            name="OpenAI",
            base_url="https://api.openai.com/v1",
            model_name="gpt-4o-mini",
            api_key_encrypted="x",
            is_enabled=True,
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="usage-proj",
            entry_type="original",
            stage="topic",
        )
        self.other_project = V3Project.objects.create(
            owner=self.other,
            title="other-proj",
            entry_type="original",
            stage="topic",
        )

    def _rollup(
        self,
        *,
        owner=None,
        project=None,
        day: date | None = None,
        model_name: str = "gpt-4o-mini",
        command_type: str | None = "generate_topic",
        prompt_tokens: int = 100,
        completion_tokens: int = 50,
        total_tokens: int = 150,
        call_count: int = 1,
        success_count: int = 1,
        estimated_cost: str = "0.010000",
        unpriced_call_count: int = 0,
    ) -> V3UsageDailyRollup:
        return V3UsageDailyRollup.objects.create(
            date=day or date(2026, 7, 20),
            owner=owner or self.user,
            project=project if project is not None else self.project,
            command_type=command_type,
            model_name=model_name,
            provider=self.provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            call_count=call_count,
            success_count=success_count,
            estimated_cost=Decimal(estimated_cost),
            unpriced_call_count=unpriced_call_count,
        )

    def test_unauthenticated_rejected(self) -> None:
        self.client.force_authenticate(user=None)
        resp = self.client.get(_SUMMARY)
        self.assertIn(resp.status_code, (401, 403))

    def test_empty_summary_shape(self) -> None:
        resp = self.client.get(
            _SUMMARY,
            {
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
                "group_by": "day",
            },
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        data = body["data"]
        self.assertEqual(data["timezone"], "Asia/Shanghai")
        self.assertEqual(data["date_from"], "2026-07-01")
        self.assertEqual(data["date_to"], "2026-07-31")
        self.assertEqual(data["group_by"], "day")
        self.assertEqual(data["rows"], [])
        totals = data["totals"]
        self.assertEqual(totals["prompt_tokens"], 0)
        self.assertEqual(totals["completion_tokens"], 0)
        self.assertEqual(totals["total_tokens"], 0)
        self.assertEqual(totals["call_count"], 0)
        self.assertEqual(totals["success_count"], 0)
        self.assertEqual(totals["unpriced_call_count"], 0)
        self.assertEqual(Decimal(str(totals["estimated_cost"])), Decimal("0.00"))

    def test_reads_rollup_group_by_day(self) -> None:
        self._rollup(day=date(2026, 7, 20), prompt_tokens=100, total_tokens=150)
        self._rollup(
            day=date(2026, 7, 21),
            prompt_tokens=200,
            completion_tokens=100,
            total_tokens=300,
            call_count=2,
            success_count=2,
            estimated_cost="0.020000",
        )
        resp = self.client.get(
            _SUMMARY,
            {
                "date_from": "2026-07-20",
                "date_to": "2026-07-21",
                "group_by": "day",
            },
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        data = resp.json()["data"]
        rows = {r["key"]: r for r in data["rows"]}
        self.assertEqual(set(rows), {"2026-07-20", "2026-07-21"})
        self.assertEqual(rows["2026-07-20"]["prompt_tokens"], 100)
        self.assertEqual(rows["2026-07-20"]["call_count"], 1)
        self.assertEqual(rows["2026-07-21"]["total_tokens"], 300)
        self.assertEqual(data["totals"]["call_count"], 3)
        self.assertEqual(data["totals"]["prompt_tokens"], 300)

    def test_group_by_model(self) -> None:
        self._rollup(model_name="gpt-4o-mini", prompt_tokens=10, total_tokens=15)
        self._rollup(
            day=date(2026, 7, 21),
            model_name="gpt-4o",
            prompt_tokens=40,
            completion_tokens=20,
            total_tokens=60,
        )
        resp = self.client.get(
            _SUMMARY,
            {
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
                "group_by": "model",
            },
        )
        self.assertEqual(resp.status_code, 200)
        rows = {r["key"]: r for r in resp.json()["data"]["rows"]}
        self.assertEqual(rows["gpt-4o-mini"]["prompt_tokens"], 10)
        self.assertEqual(rows["gpt-4o"]["prompt_tokens"], 40)

    def test_group_by_command_type(self) -> None:
        self._rollup(command_type="generate_topic", call_count=1)
        self._rollup(
            day=date(2026, 7, 21),
            command_type="generate_blueprint",
            call_count=3,
            success_count=3,
            prompt_tokens=30,
            completion_tokens=15,
            total_tokens=45,
        )
        resp = self.client.get(
            _SUMMARY,
            {
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
                "group_by": "command_type",
            },
        )
        self.assertEqual(resp.status_code, 200)
        rows = {r["key"]: r for r in resp.json()["data"]["rows"]}
        self.assertEqual(rows["generate_topic"]["call_count"], 1)
        self.assertEqual(rows["generate_blueprint"]["call_count"], 3)

    def test_owner_isolation(self) -> None:
        self._rollup(owner=self.user, prompt_tokens=100, total_tokens=150)
        self._rollup(
            owner=self.other,
            project=self.other_project,
            day=date(2026, 7, 21),
            prompt_tokens=999,
            total_tokens=999,
            call_count=9,
        )
        resp = self.client.get(
            _SUMMARY,
            {
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
                "group_by": "day",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(len(data["rows"]), 1)
        self.assertEqual(data["totals"]["prompt_tokens"], 100)
        self.assertEqual(data["totals"]["call_count"], 1)

    def test_project_id_filter(self) -> None:
        other_own = V3Project.objects.create(
            owner=self.user,
            title="p2",
            entry_type="original",
            stage="topic",
        )
        self._rollup(project=self.project, prompt_tokens=10, total_tokens=15)
        self._rollup(
            project=other_own,
            day=date(2026, 7, 21),
            prompt_tokens=90,
            total_tokens=90,
        )
        resp = self.client.get(
            _SUMMARY,
            {
                "project_id": str(self.project.id),
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
                "group_by": "day",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(len(data["rows"]), 1)
        self.assertEqual(data["totals"]["prompt_tokens"], 10)

    def test_invalid_group_by_rejected(self) -> None:
        resp = self.client.get(
            _SUMMARY,
            {
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
                "group_by": "provider",
            },
        )
        self.assertEqual(resp.status_code, 400)

    def test_unpriced_call_count_in_totals(self) -> None:
        self._rollup(unpriced_call_count=2, estimated_cost="0")
        resp = self.client.get(
            _SUMMARY,
            {
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
                "group_by": "day",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertEqual(data["rows"][0]["unpriced_call_count"], 2)
        self.assertEqual(data["totals"]["unpriced_call_count"], 2)

    def test_rollup_cost_recomputed_after_price_configured(self) -> None:
        """调用当时未定价写入 rollup；事后配置单价后，汇总应按当前价重算。"""
        self._rollup(
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            call_count=2,
            estimated_cost="0",
            unpriced_call_count=2,
        )
        V3ModelPrice.objects.create(
            provider=self.provider,
            model_name="gpt-4o-mini",
            price_in_per_1k=Decimal("1.000000"),
            price_out_per_1k=Decimal("2.000000"),
        )
        resp = self.client.get(
            _SUMMARY,
            {
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
                "group_by": "day",
            },
        )
        self.assertEqual(resp.status_code, 200)
        row = resp.json()["data"]["rows"][0]
        self.assertEqual(row["unpriced_call_count"], 0)
        # 1*1 + 0.5*2 = 2.00
        self.assertEqual(Decimal(str(row["estimated_cost"])), Decimal("2.00"))

    def test_live_aggregates_call_logs_in_date_range(self) -> None:
        """live=1：忽略 rollup，仅按日期范围聚合 call log。"""
        self._rollup(
            day=date(2026, 7, 20),
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            call_count=1,
            estimated_cost="0.010000",
        )
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic",
            status=V3CommandRun.Status.SUCCEEDED,
        )
        V3ModelPrice.objects.create(
            provider=self.provider,
            model_name="gpt-4o-mini",
            price_in_per_1k=Decimal("0.001000"),
            price_out_per_1k=Decimal("0.002000"),
        )
        log_day = date(2026, 7, 22)
        log = DramaLlmCallLog.objects.create(
            v3_command_run=run,
            v3_project=self.project,
            actor="usage",
            model_name="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            status=DramaLlmCallLog.Status.SUCCESS,
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
        )
        DramaLlmCallLog.objects.filter(pk=log.pk).update(
            created_at=datetime(
                log_day.year, log_day.month, log_day.day, 12, 0, tzinfo=timezone.utc
            )
        )

        resp = self.client.get(
            _SUMMARY,
            {
                "date_from": "2026-07-20",
                "date_to": "2026-07-23",
                "group_by": "day",
                "live": "1",
            },
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        data = resp.json()["data"]
        rows = {r["key"]: r for r in data["rows"]}
        self.assertEqual(set(rows), {"2026-07-22"})
        self.assertEqual(rows["2026-07-22"]["prompt_tokens"], 1000)
        self.assertEqual(rows["2026-07-22"]["call_count"], 1)
        self.assertEqual(data["totals"]["call_count"], 1)
        self.assertEqual(data["totals"]["prompt_tokens"], 1000)

    def test_live_no_double_count_when_rollup_has_same_call(self) -> None:
        """live=1：rollup 已含同笔 call 时不得重复计数。"""
        log_day = date(2026, 7, 22)
        self._rollup(
            day=log_day,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            call_count=1,
            estimated_cost="0.010000",
        )
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic",
            status=V3CommandRun.Status.SUCCEEDED,
        )
        log = DramaLlmCallLog.objects.create(
            v3_command_run=run,
            v3_project=self.project,
            actor="usage",
            model_name="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            status=DramaLlmCallLog.Status.SUCCESS,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        DramaLlmCallLog.objects.filter(pk=log.pk).update(
            created_at=datetime(
                log_day.year, log_day.month, log_day.day, 12, 0, tzinfo=timezone.utc
            )
        )

        resp = self.client.get(
            _SUMMARY,
            {
                "date_from": log_day.isoformat(),
                "date_to": log_day.isoformat(),
                "group_by": "day",
                "live": "1",
            },
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        data = resp.json()["data"]
        self.assertEqual(len(data["rows"]), 1)
        self.assertEqual(data["rows"][0]["prompt_tokens"], 100)
        self.assertEqual(data["rows"][0]["call_count"], 1)
        self.assertEqual(data["totals"]["prompt_tokens"], 100)
        self.assertEqual(data["totals"]["call_count"], 1)

    def test_live_0_ignores_recent_logs_without_rollup(self) -> None:
        run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic",
            status=V3CommandRun.Status.SUCCEEDED,
        )
        log = DramaLlmCallLog.objects.create(
            v3_command_run=run,
            v3_project=self.project,
            actor="usage",
            model_name="gpt-4o-mini",
            status=DramaLlmCallLog.Status.SUCCESS,
            prompt_tokens=500,
            completion_tokens=100,
            total_tokens=600,
        )
        DramaLlmCallLog.objects.filter(pk=log.pk).update(
            created_at=dj_timezone.now() - timedelta(hours=1)
        )
        resp = self.client.get(
            _SUMMARY,
            {
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
                "group_by": "day",
                "live": "0",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["rows"], [])
        self.assertEqual(resp.json()["data"]["totals"]["call_count"], 0)
