# -*- coding: utf-8 -*-
"""P2-W2 Task 3：Models Prices REST GET/PUT。"""
from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.drama.models import DramaLlmProvider, V3ModelPrice
from apps.drama.services.secret_crypto import encrypt_secret

_PRICES = "/api/v3/models/prices/"


class V3PricesApiTests(APITestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="prices_api", password="pass12345"
        )
        self.client.force_authenticate(user=self.user)
        self.provider = DramaLlmProvider.objects.create(
            name="OpenAI",
            base_url="https://api.openai.com/v1",
            model_name="gpt-4o-mini",
            api_key_encrypted=encrypt_secret("sk-test"),
            is_enabled=True,
        )

    def test_get_empty_list(self) -> None:
        resp = self.client.get(_PRICES)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["items"], [])

    def test_put_creates_and_get_returns_rows(self) -> None:
        put_resp = self.client.put(
            _PRICES,
            {
                "items": [
                    {
                        "provider_id": str(self.provider.id),
                        "model_name": "gpt-4o-mini",
                        "price_in_per_1k": "0.001500",
                        "price_out_per_1k": "0.006000",
                        "currency": "CNY",
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(put_resp.status_code, 200, put_resp.content)
        put_items = put_resp.json()["data"]["items"]
        self.assertEqual(len(put_items), 1)
        item = put_items[0]
        self.assertIn("id", item)
        self.assertEqual(item["provider_id"], str(self.provider.id))
        self.assertEqual(item["provider_name"], "OpenAI")
        self.assertEqual(item["model_name"], "gpt-4o-mini")
        self.assertEqual(Decimal(str(item["price_in_per_1k"])), Decimal("0.001500"))
        self.assertEqual(Decimal(str(item["price_out_per_1k"])), Decimal("0.006000"))
        self.assertIsNone(item.get("price_cache_in_per_1k"))
        self.assertEqual(item["currency"], "CNY")

        got = self.client.get(_PRICES)
        self.assertEqual(got.status_code, 200)
        got_items = got.json()["data"]["items"]
        self.assertEqual(len(got_items), 1)
        self.assertEqual(got_items[0]["id"], item["id"])

        row = V3ModelPrice.objects.get(pk=item["id"])
        self.assertEqual(row.provider_id, self.provider.id)
        self.assertEqual(row.model_name, "gpt-4o-mini")

    def test_put_upserts_by_provider_and_model_name(self) -> None:
        first = self.client.put(
            _PRICES,
            {
                "items": [
                    {
                        "provider_id": str(self.provider.id),
                        "model_name": "gpt-4o-mini",
                        "price_in_per_1k": 0.001,
                        "price_out_per_1k": 0.002,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(first.status_code, 200)
        first_id = first.json()["data"]["items"][0]["id"]
        self.assertEqual(V3ModelPrice.objects.count(), 1)

        second = self.client.put(
            _PRICES,
            {
                "items": [
                    {
                        "provider_id": str(self.provider.id),
                        "model_name": "gpt-4o-mini",
                        "price_in_per_1k": 0.003,
                        "price_out_per_1k": 0.004,
                        "currency": "USD",
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(second.status_code, 200)
        second_item = second.json()["data"]["items"][0]
        self.assertEqual(second_item["id"], first_id)
        self.assertEqual(second_item["currency"], "USD")
        self.assertEqual(V3ModelPrice.objects.count(), 1)
        row = V3ModelPrice.objects.get(pk=first_id)
        self.assertEqual(row.price_in_per_1k, Decimal("0.003000"))
        self.assertEqual(row.price_out_per_1k, Decimal("0.004000"))

    def test_put_rejects_missing_provider(self) -> None:
        missing_id = "00000000-0000-0000-0000-000000000099"
        resp = self.client.put(
            _PRICES,
            {
                "items": [
                    {
                        "provider_id": missing_id,
                        "model_name": "gpt-4o-mini",
                        "price_in_per_1k": 0.001,
                        "price_out_per_1k": 0.002,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(V3ModelPrice.objects.count(), 0)

    def test_put_rejects_negative_prices(self) -> None:
        resp = self.client.put(
            _PRICES,
            {
                "items": [
                    {
                        "provider_id": str(self.provider.id),
                        "model_name": "gpt-4o-mini",
                        "price_in_per_1k": -0.001,
                        "price_out_per_1k": 0.002,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(V3ModelPrice.objects.count(), 0)

    def test_put_rejects_empty_items(self) -> None:
        resp = self.client.put(_PRICES, {"items": []}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_unauthenticated_rejected(self) -> None:
        self.client.force_authenticate(user=None)
        resp = self.client.get(_PRICES)
        self.assertIn(resp.status_code, (401, 403))

    def test_delete_removes_price_row(self) -> None:
        put_resp = self.client.put(
            _PRICES,
            {
                "items": [
                    {
                        "provider_id": str(self.provider.id),
                        "model_name": "gpt-4o-mini",
                        "price_in_per_1k": "0.001",
                        "price_out_per_1k": "0.002",
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(put_resp.status_code, 200)
        price_id = put_resp.json()["data"]["items"][0]["id"]
        self.assertEqual(V3ModelPrice.objects.count(), 1)

        del_resp = self.client.delete(f"{_PRICES}{price_id}/")
        self.assertEqual(del_resp.status_code, 200, del_resp.content)
        body = del_resp.json()
        self.assertEqual(body["code"], 0)
        self.assertTrue(body["data"]["deleted"])
        self.assertEqual(V3ModelPrice.objects.count(), 0)

    def test_put_accepts_cache_hit_price(self) -> None:
        resp = self.client.put(
            _PRICES,
            {
                "items": [
                    {
                        "provider_id": str(self.provider.id),
                        "model_name": "gpt-4o-mini",
                        "price_in_per_1k": "0.001",
                        "price_out_per_1k": "0.002",
                        "price_cache_in_per_1k": "0.0001",
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        item = resp.json()["data"]["items"][0]
        self.assertEqual(Decimal(str(item["price_cache_in_per_1k"])), Decimal("0.000100"))
        row = V3ModelPrice.objects.get(pk=item["id"])
        self.assertEqual(row.price_cache_in_per_1k, Decimal("0.000100"))
        self.assertEqual(body["data"]["id"], price_id)
        self.assertEqual(V3ModelPrice.objects.count(), 0)

    def test_delete_missing_returns_404(self) -> None:
        resp = self.client.delete(f"{_PRICES}999999/")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(V3ModelPrice.objects.count(), 0)
