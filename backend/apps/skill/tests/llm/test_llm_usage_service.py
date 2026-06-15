# -*- coding: utf-8 -*-
from decimal import Decimal

from django.db import connection, transaction
from django.test import TestCase

from apps.skill.llm.model_catalog import LlmCatalogService
from apps.skill.llm.usage_log import LlmUsageService, llm_usage_scope
from apps.skill.models import LlmModelCatalog, LlmProvider, LlmUsageLog


class LlmUsageServiceTests(TestCase):
    def test_record_and_dashboard_aggregate(self):
        LlmUsageService.record(
            cfg={
                "provider_id": None,
                "provider_name": "DeepSeek V4 Flash（火山）",
                "model": "ep-test-flash",
            },
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            source_type=LlmUsageLog.SOURCE_NODE,
            source_key="node-2-structure",
        )
        LlmUsageService.record(
            cfg={
                "provider_id": None,
                "provider_name": "GLM-5（智谱原生）",
                "model": "glm-5",
            },
            usage={"prompt_tokens": 200, "completion_tokens": 80, "total_tokens": 280},
            source_type=LlmUsageLog.SOURCE_NODE,
            source_key="node-5-script",
        )

        payload = LlmUsageService.dashboard_payload(days=30)
        self.assertEqual(payload["summary"]["today_call_count"], 2)
        self.assertEqual(payload["summary"]["today_total_tokens"], 430)
        self.assertGreaterEqual(payload["summary"]["today_estimated_cost_yuan"], 0)
        self.assertEqual(len(payload["llm_usage_top"]), 2)
        self.assertTrue(payload["llm_usage_7d"])

    def test_parse_usage_fallback_total(self):
        tokens = LlmUsageService._parse_usage({"prompt_tokens": 10, "completion_tokens": 5})
        self.assertEqual(tokens["total_tokens"], 15)

    def test_parse_usage_input_output_aliases(self):
        tokens = LlmUsageService._parse_usage({"input_tokens": 100, "output_tokens": 40})
        self.assertEqual(tokens["prompt_tokens"], 100)
        self.assertEqual(tokens["completion_tokens"], 40)
        self.assertEqual(tokens["total_tokens"], 140)

    def test_resolve_sub_skill_id_from_source_key(self):
        resolved = LlmUsageService._resolve_sub_skill_id(
            {},
            source_key="node-2-structure:world-builder",
        )
        self.assertEqual(resolved, "world-builder")

    def test_record_failure_does_not_break_outer_atomic(self):
        from unittest.mock import patch

        from django.db import IntegrityError

        with transaction.atomic():
            with llm_usage_scope(
                source_type=LlmUsageLog.SOURCE_NODE,
                source_key="node-2-structure",
            ):
                with patch.object(
                    LlmUsageLog.objects,
                    "create",
                    side_effect=IntegrityError("boom"),
                ):
                    LlmUsageService.record(
                        cfg={"provider_name": "t", "model": "m"},
                        usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    )
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

    def test_record_without_sub_skill_id_uses_empty_string(self):
        with llm_usage_scope(
            source_type=LlmUsageLog.SOURCE_NODE,
            source_key="node-2-structure:structure-generator",
        ):
            LlmUsageService.record(
                cfg={"provider_name": "volcano", "model": "ep-test"},
                usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            )
        usage = LlmUsageLog.objects.latest("created_at")
        self.assertEqual(usage.sub_skill_id, "structure-generator")

    def test_recalculate_all_logs(self):
        LlmCatalogService.ensure_seed_catalog()
        catalog = LlmModelCatalog.objects.get(preset_key="ark-deepseek-v4-flash")
        catalog.input_price_per_million = None
        catalog.output_price_per_million = None
        catalog.save(update_fields=["input_price_per_million", "output_price_per_million"])

        provider = LlmProvider.objects.create(
            name="flash ep",
            catalog=catalog,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            model_name="ep-recalc-all",
            is_enabled=True,
        )
        provider.set_api_key("k")
        provider.save()

        LlmUsageService.record(
            cfg={
                "provider_id": str(provider.id),
                "provider_name": "flash ep",
                "model": "ep-recalc-all",
            },
            usage={"prompt_tokens": 1_000_000, "completion_tokens": 0, "total_tokens": 1_000_000},
        )
        log = LlmUsageLog.objects.latest("created_at")
        self.assertEqual(log.estimated_input_cost_yuan, Decimal("0.000000"))
        self.assertEqual(log.estimated_output_cost_yuan, Decimal("0.000000"))
        self.assertEqual(log.estimated_cost_yuan, Decimal("0.000000"))

        catalog.input_price_per_million = Decimal("1.0000")
        catalog.output_price_per_million = Decimal("2.0000")
        catalog.save(update_fields=["input_price_per_million", "output_price_per_million"])

        updated = LlmUsageService.recalculate_estimated_costs(all_logs=True)
        self.assertEqual(updated, 1)
        log.refresh_from_db()
        self.assertEqual(log.estimated_input_cost_yuan, Decimal("1.000000"))
        self.assertEqual(log.estimated_output_cost_yuan, Decimal("0.000000"))
        self.assertEqual(log.estimated_cost_yuan, Decimal("1.000000"))

    def test_llm_usage_by_source_aggregates_normalized_keys(self):
        for key, tokens in (
            ("node-2-structure", 100),
            ("node 2 structure", 80),
            ("node-2-structure:world-builder", 50),
        ):
            LlmUsageService.record(
                cfg={"provider_name": "DeepSeek V4 Flash（火山）", "model": "ep-node"},
                usage={"prompt_tokens": tokens, "completion_tokens": 0, "total_tokens": tokens},
                source_type=LlmUsageLog.SOURCE_NODE,
                source_key=key,
            )
        payload = LlmUsageService.dashboard_payload(days=30)
        node_rows = [
            row
            for row in payload["llm_usage_by_source"]
            if row["source_type"] == LlmUsageLog.SOURCE_NODE
        ]
        self.assertEqual(len(node_rows), 1)
        self.assertEqual(node_rows[0]["source_key"], "node-2-structure")
        self.assertEqual(node_rows[0]["call_count"], 3)
        self.assertEqual(node_rows[0]["total_tokens"], 230)

    def test_cleanup_junk_logs(self):
        LlmUsageService.record(
            cfg={"provider_name": "t", "model": "m"},
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )
        LlmUsageService.record(
            cfg={"provider_name": "test", "model": "test"},
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )
        LlmUsageService.record(
            cfg={"provider_name": "DeepSeek V4 Flash（火山）", "model": "ep-real"},
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        self.assertEqual(LlmUsageService.junk_log_queryset().count(), 2)
        deleted = LlmUsageService.cleanup_junk_logs()
        self.assertEqual(deleted, 2)
        self.assertEqual(LlmUsageLog.objects.count(), 1)
        payload = LlmUsageService.dashboard_payload(days=30)
        names = [row["display_name"] for row in payload["llm_usage_top"]]
        self.assertNotIn("t / m", names)
        self.assertNotIn("test / test", names)
