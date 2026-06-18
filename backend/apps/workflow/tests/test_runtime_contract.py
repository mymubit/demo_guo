# -*- coding: utf-8 -*-
from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase


class RuntimeContractTests(SimpleTestCase):
    def test_enforce_input_budget_blocks_large_payload(self):
        from apps.workflow.runtime_contract import RuntimeBudgetExceeded, enforce_input_budget

        node = MagicMock()
        node.runtime_config = {"max_input_bytes": 128, "warn_input_bytes": 64}

        with self.assertRaises(RuntimeBudgetExceeded) as ctx:
            enforce_input_budget({"text": "x" * 500}, node)

        self.assertGreater(ctx.exception.snapshot["bytes"], 128)

    def test_snapshot_payload_records_shape_without_full_body(self):
        from apps.workflow.runtime_contract import snapshot_payload

        snap = snapshot_payload({"brief": {"coreIdea": "x" * 300}, "episodes": [1, 2, 3]})

        self.assertEqual(snap["key_count"], 2)
        self.assertIn("brief", snap["top_keys"])
        self.assertLessEqual(len(snap["shape"]["children"]["brief"]["children"]["coreIdea"]["preview"]), 160)

    def test_agent_registry_cache_clear_compat(self):
        from apps.agent.runtime import get_agent_registry

        self.assertTrue(callable(getattr(get_agent_registry, "cache_clear", None)))

