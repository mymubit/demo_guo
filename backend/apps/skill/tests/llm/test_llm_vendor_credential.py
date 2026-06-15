# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.skill.llm.model_catalog import LlmCatalogService
from apps.skill.llm.providers import LlmProviderService
from apps.skill.llm.vendor_keys import LlmVendorCredentialService
from apps.skill.models import LlmModelCatalog, LlmProvider


class LlmVendorCredentialTests(TestCase):
    def setUp(self):
        LlmCatalogService.ensure_seed_catalog()
        self.catalog = LlmModelCatalog.objects.get(preset_key="ark-deepseek-v4-flash")

    def test_set_vendor_credential_syncs_providers(self):
        provider = LlmProvider.objects.create(
            name="DeepSeek Flash",
            catalog=self.catalog,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model_name="deepseek-v4-flash",
            is_enabled=True,
        )
        LlmVendorCredentialService.set_vendor_credential(
            "volcengine",
            api_key="shared-volcano-key",
            volcano_key_type="payg",
        )
        provider.refresh_from_db()
        self.assertTrue(provider.api_key_set)
        self.assertEqual(provider.get_api_key(), "shared-volcano-key")

    def test_runtime_config_uses_vendor_key(self):
        provider = LlmProvider.objects.create(
            name="DeepSeek Flash",
            catalog=self.catalog,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model_name="deepseek-v4-flash",
            is_enabled=True,
        )
        LlmVendorCredentialService.set_vendor_credential(
            "volcengine",
            api_key="shared-volcano-key",
            volcano_key_type="payg",
        )
        cfg = LlmProviderService.runtime_config(provider)
        self.assertEqual(cfg["api_key"], "shared-volcano-key")

    def test_create_provider_inherits_vendor_key(self):
        LlmVendorCredentialService.set_vendor_credential(
            "volcengine",
            api_key="shared-volcano-key",
            volcano_key_type="payg",
        )
        provider = LlmProviderService.create_provider(
            {
                "catalog_id": str(self.catalog.id),
                "model_name": "ep-test-inherit",
            }
        )
        self.assertTrue(provider.api_key_set)
        self.assertEqual(provider.get_api_key(), "shared-volcano-key")
