# -*- coding: utf-8 -*-
"""将 VOLCANO_EP_* 环境变量同步到火山 Provider 的 model_name（ep-xxx）。"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.skill.llm.vendor_keys import LlmVendorCredentialService
from apps.skill.models import LlmModelCatalog, LlmProvider
from apps.skill.llm.volcengine_chat import PRESET_ENDPOINT_ENV, env_endpoint, is_volcano_endpoint_id


class Command(BaseCommand):
    help = "从 VOLCANO_EP_* / VOLCANO_ARK_KEY_TYPE 同步火山推理接入点到 DB Provider"

    def handle(self, *args, **options):
        from django.conf import settings

        key_type = (
            getattr(settings, "VOLCANO_ARK_KEY_TYPE", "") or "payg"
        ).strip() or "payg"
        LlmVendorCredentialService.set_vendor_credential(
            "volcengine",
            volcano_key_type=key_type,
            sync_providers=True,
        )
        self.stdout.write(f"厂商火山 Key 类型: {key_type}")

        updated = 0
        catalogs = {
            row.preset_key: row
            for row in LlmModelCatalog.objects.filter(vendor="volcengine")
        }
        for preset_key, env_var in PRESET_ENDPOINT_ENV.items():
            ep = env_endpoint(env_var)
            if not ep or not is_volcano_endpoint_id(ep):
                continue
            catalog = catalogs.get(preset_key)
            if not catalog:
                continue
            rows = LlmProvider.objects.filter(catalog_id=catalog.id)
            for row in rows:
                if row.model_name == ep:
                    continue
                old = row.model_name
                row.model_name = ep
                row.volcano_key_type = key_type
                row.save(update_fields=["model_name", "volcano_key_type", "updated_at"])
                updated += 1
                self.stdout.write(f"  {row.name}: {old} -> {ep}")

        self.stdout.write(self.style.SUCCESS(f"完成，更新 {updated} 条 Provider"))
