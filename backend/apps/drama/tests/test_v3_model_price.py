# -*- coding: utf-8 -*-
"""P2-W2 Task 1：V3ModelPrice 模型。"""
from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from apps.drama.models import DramaLlmProvider, V3ModelPrice


class V3ModelPriceTests(TestCase):
    def setUp(self) -> None:
        self.provider = DramaLlmProvider.objects.create(
            name="OpenAI",
            base_url="https://api.openai.com/v1",
            model_name="gpt-4o-mini",
            api_key_encrypted="x",
            is_enabled=True,
        )

    def test_create_price_row_with_defaults(self) -> None:
        row = V3ModelPrice.objects.create(
            provider=self.provider,
            model_name="gpt-4o-mini",
            price_in_per_1k=Decimal("0.001500"),
            price_out_per_1k=Decimal("0.006000"),
        )
        self.assertEqual(row.currency, "CNY")
        self.assertEqual(row.price_in_per_1k, Decimal("0.001500"))
        self.assertEqual(row.price_out_per_1k, Decimal("0.006000"))

    def test_unique_conflict_on_duplicate_provider_model(self) -> None:
        V3ModelPrice.objects.create(
            provider=self.provider,
            model_name="gpt-4o-mini",
            price_in_per_1k=Decimal("0.001"),
            price_out_per_1k=Decimal("0.002"),
        )
        with self.assertRaises(IntegrityError):
            V3ModelPrice.objects.create(
                provider=self.provider,
                model_name="gpt-4o-mini",
                price_in_per_1k=Decimal("0.003"),
                price_out_per_1k=Decimal("0.004"),
            )
