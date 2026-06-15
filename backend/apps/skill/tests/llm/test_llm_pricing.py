# -*- coding: utf-8 -*-
from decimal import Decimal

from django.test import TestCase

from apps.skill.llm.pricing import estimate_cost_breakdown, estimate_cost_yuan, resolve_pricing
from apps.skill.llm.model_catalog import LlmCatalogService
from apps.skill.models import LlmModelCatalog, LlmProvider


class LlmPricingTests(TestCase):
    def setUp(self):
        LlmCatalogService.ensure_seed_catalog()
        self.catalog = LlmModelCatalog.objects.get(preset_key="ark-deepseek-v4-flash")
        self.catalog.input_price_per_million = Decimal("1.0000")
        self.catalog.output_price_per_million = Decimal("2.0000")
        self.catalog.save(update_fields=["input_price_per_million", "output_price_per_million"])
        self.provider = LlmProvider.objects.create(
            name="DeepSeek 火山",
            catalog=self.catalog,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model_name="ep-test-pricing",
            is_enabled=True,
        )
        self.provider.set_api_key("test-key")
        self.provider.save()

    def test_estimate_cost(self):
        inp_cost, out_cost, total = estimate_cost_breakdown(
            prompt_tokens=1_000_000,
            completion_tokens=500_000,
            input_price_per_million=Decimal("1"),
            output_price_per_million=Decimal("2"),
        )
        self.assertEqual(inp_cost, Decimal("1.000000"))
        self.assertEqual(out_cost, Decimal("1.000000"))
        self.assertEqual(total, Decimal("2.000000"))
        self.assertEqual(
            estimate_cost_yuan(
                prompt_tokens=1_000_000,
                completion_tokens=500_000,
                input_price_per_million=Decimal("1"),
                output_price_per_million=Decimal("2"),
            ),
            total,
        )

    def test_resolve_pricing_via_provider_catalog_for_ep(self):
        inp, out = resolve_pricing(provider_id=self.provider.id, model_name="ep-test-pricing")
        self.assertEqual(inp, Decimal("1.0000"))
        self.assertEqual(out, Decimal("2.0000"))

    def test_seed_deepseek_v4_pro_volcano_pricing(self):
        LlmCatalogService.ensure_seed_catalog()
        row = LlmModelCatalog.objects.get(preset_key="ark-deepseek-v4-pro")
        self.assertEqual(row.input_price_per_million, Decimal("12.0000"))
        self.assertEqual(row.output_price_per_million, Decimal("24.0000"))

    def test_ep_without_catalog_does_not_use_cheapest_volcano(self):
        """ep-xxx 且 Provider 无 catalog 时，不得误用 sort 最靠前的火山目录价。"""
        pro_cat = LlmModelCatalog.objects.get(preset_key="ark-deepseek-v4-pro")
        pro_provider = LlmProvider.objects.create(
            name="DeepSeek Pro ep",
            catalog=pro_cat,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model_name="ep-pro-only",
            is_enabled=True,
        )
        pro_provider.set_api_key("k")
        pro_provider.save()

        orphan = LlmProvider.objects.create(
            name="orphan ep",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model_name="ep-pro-only",
            is_enabled=True,
        )
        orphan.set_api_key("k")
        orphan.save()

        inp, out = resolve_pricing(provider_id=orphan.id, model_name="ep-pro-only")
        self.assertEqual(inp, Decimal("12.0000"))
        self.assertEqual(out, Decimal("24.0000"))

    def test_ep_without_any_catalog_returns_none(self):
        orphan = LlmProvider.objects.create(
            name="lonely ep",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model_name="ep-unknown-xyz",
            is_enabled=True,
        )
        inp, out = resolve_pricing(provider_id=orphan.id, model_name="ep-unknown-xyz")
        self.assertIsNone(inp)
        self.assertIsNone(out)
