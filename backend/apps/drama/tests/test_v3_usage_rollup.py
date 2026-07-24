# -*- coding: utf-8 -*-
"""P2-W2 Task 2：V3UsageDailyRollup + increment helper。"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.drama.models import (
    DramaLlmCallLog,
    DramaLlmProvider,
    V3CommandRun,
    V3ModelPrice,
    V3Project,
    V3UsageDailyRollup,
)
from apps.drama.orchestrator.usage_rollup import (
    apply_call_to_rollup,
    estimate_cost,
    shanghai_date,
)
from apps.drama.services.llm_call_log_service import LlmCallLogService


class ShanghaiDateTests(TestCase):
    def test_shanghai_date_converts_utc_across_midnight(self) -> None:
        # UTC 2026-07-22 16:30 → Asia/Shanghai 2026-07-23 00:30
        dt = datetime(2026, 7, 22, 16, 30, tzinfo=timezone.utc)
        self.assertEqual(shanghai_date(dt), datetime(2026, 7, 23).date())


class EstimateCostTests(TestCase):
    def setUp(self) -> None:
        self.provider = DramaLlmProvider.objects.create(
            name="OpenAI",
            base_url="https://api.openai.com/v1",
            model_name="gpt-4o-mini",
            api_key_encrypted="x",
            is_enabled=True,
        )
        V3ModelPrice.objects.create(
            provider=self.provider,
            model_name="gpt-4o-mini",
            price_in_per_1k=Decimal("0.001000"),
            price_out_per_1k=Decimal("0.002000"),
        )

    def test_estimate_cost_priced(self) -> None:
        cost = estimate_cost(
            provider_id=self.provider.id,
            model_name="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
        )
        # 1*0.001 + 0.5*0.002 = 0.002
        self.assertEqual(cost, Decimal("0.002000"))

    def test_estimate_cost_unpriced_returns_none(self) -> None:
        cost = estimate_cost(
            provider_id=self.provider.id,
            model_name="unknown-model",
            prompt_tokens=100,
            completion_tokens=50,
        )
        self.assertIsNone(cost)

    def test_estimate_cost_uses_cache_rate_for_cached_tokens(self) -> None:
        V3ModelPrice.objects.filter(provider=self.provider).update(
            price_cache_in_per_1k=Decimal("0.000100"),
        )
        cost = estimate_cost(
            provider_id=self.provider.id,
            model_name="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=0,
            cached_prompt_tokens=800,
        )
        # fresh 200 * 0.001/1k + cached 800 * 0.0001/1k = 0.0002 + 0.00008
        self.assertEqual(cost, Decimal("0.000280"))


class ApplyCallToRollupTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user("rollup", password="x")
        self.provider = DramaLlmProvider.objects.create(
            name="OpenAI",
            base_url="https://api.openai.com/v1",
            model_name="gpt-4o-mini",
            api_key_encrypted="x",
            is_enabled=True,
        )
        self.project = V3Project.objects.create(
            owner=self.user,
            title="p",
            entry_type="original",
            stage="topic",
        )
        self.run = V3CommandRun.objects.create(
            owner=self.user,
            project=self.project,
            command_type="generate_topic",
            status=V3CommandRun.Status.RUNNING,
        )

    def _make_log(
        self,
        *,
        model_name: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        prompt_tokens: int = 1000,
        completion_tokens: int = 500,
        total_tokens: int = 1500,
        status: str = DramaLlmCallLog.Status.SUCCESS,
    ) -> DramaLlmCallLog:
        return DramaLlmCallLog.objects.create(
            v3_command_run=self.run,
            v3_project=self.project,
            actor="rollup",
            model_name=model_name,
            base_url=base_url,
            status=status,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    def test_priced_call_increments_cost(self) -> None:
        V3ModelPrice.objects.create(
            provider=self.provider,
            model_name="gpt-4o-mini",
            price_in_per_1k=Decimal("0.001000"),
            price_out_per_1k=Decimal("0.002000"),
        )
        log = self._make_log()
        apply_call_to_rollup(log)

        row = V3UsageDailyRollup.objects.get()
        self.assertEqual(row.owner_id, self.user.id)
        self.assertEqual(row.project_id, self.project.id)
        self.assertEqual(row.command_type, "generate_topic")
        self.assertEqual(row.model_name, "gpt-4o-mini")
        self.assertEqual(row.provider_id, self.provider.id)
        self.assertEqual(row.prompt_tokens, 1000)
        self.assertEqual(row.completion_tokens, 500)
        self.assertEqual(row.total_tokens, 1500)
        self.assertEqual(row.call_count, 1)
        self.assertEqual(row.success_count, 1)
        self.assertEqual(row.estimated_cost, Decimal("0.002000"))
        self.assertEqual(row.unpriced_call_count, 0)
        self.assertEqual(row.date, shanghai_date(log.created_at))

    def test_unpriced_increments_unpriced_call_count(self) -> None:
        log = self._make_log(model_name="no-price-model")
        apply_call_to_rollup(log)

        row = V3UsageDailyRollup.objects.get()
        self.assertEqual(row.call_count, 1)
        self.assertEqual(row.unpriced_call_count, 1)
        self.assertEqual(row.estimated_cost, Decimal("0"))
        self.assertEqual(row.prompt_tokens, 1000)

    def test_same_day_upsert_accumulates(self) -> None:
        V3ModelPrice.objects.create(
            provider=self.provider,
            model_name="gpt-4o-mini",
            price_in_per_1k=Decimal("0.001000"),
            price_out_per_1k=Decimal("0.002000"),
        )
        log1 = self._make_log()
        log2 = self._make_log(
            prompt_tokens=2000,
            completion_tokens=0,
            total_tokens=2000,
            status=DramaLlmCallLog.Status.ERROR,
        )
        apply_call_to_rollup(log1)
        apply_call_to_rollup(log2)

        self.assertEqual(V3UsageDailyRollup.objects.count(), 1)
        row = V3UsageDailyRollup.objects.get()
        self.assertEqual(row.call_count, 2)
        self.assertEqual(row.success_count, 1)
        self.assertEqual(row.prompt_tokens, 3000)
        self.assertEqual(row.completion_tokens, 500)
        self.assertEqual(row.total_tokens, 3500)
        self.assertEqual(row.estimated_cost, Decimal("0.004000"))
        self.assertEqual(row.unpriced_call_count, 0)


class RecordWiresRollupTests(TestCase):
    def test_llm_call_log_service_record_applies_rollup(self) -> None:
        user = get_user_model().objects.create_user("wire", password="x")
        provider = DramaLlmProvider.objects.create(
            name="OpenAI",
            base_url="https://api.openai.com/v1",
            model_name="gpt-4o-mini",
            api_key_encrypted="x",
            is_enabled=True,
        )
        V3ModelPrice.objects.create(
            provider=provider,
            model_name="gpt-4o-mini",
            price_in_per_1k=Decimal("0.001000"),
            price_out_per_1k=Decimal("0.002000"),
        )
        project = V3Project.objects.create(
            owner=user,
            title="p",
            entry_type="original",
            stage="topic",
        )
        run = V3CommandRun.objects.create(
            owner=user,
            project=project,
            command_type="generate_topic",
            status=V3CommandRun.Status.RUNNING,
        )
        log = LlmCallLogService.record(
            system_prompt="s",
            user_prompt="u",
            model_name="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            status=DramaLlmCallLog.Status.SUCCESS,
            latency_ms=10,
            response_json={
                "id": "req-1",
                "choices": [{"message": {"content": "ok"}}],
                "usage": {
                    "prompt_tokens": 1000,
                    "completion_tokens": 500,
                    "total_tokens": 1500,
                },
            },
            v3_command_run_id=str(run.id),
            v3_project_id=str(project.id),
        )
        self.assertIsNotNone(log)
        self.assertEqual(V3UsageDailyRollup.objects.count(), 1)
        row = V3UsageDailyRollup.objects.get()
        self.assertEqual(row.estimated_cost, Decimal("0.002000"))
        self.assertEqual(row.call_count, 1)
