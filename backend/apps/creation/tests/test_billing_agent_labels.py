# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.billing.services import BillingService
from apps.agent.runtime import (
    action_key_agent_meta,
    agent_for_pipeline_node_index,
    get_agent_registry,
    pipeline_action_display_name,
)


class BillingAgentLabelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from apps.agent.registry import AgentRegistryConfigService

        AgentRegistryConfigService.ensure_defaults()

    def setUp(self):
        get_agent_registry.cache_clear()

    def tearDown(self):
        get_agent_registry.cache_clear()
    def test_pipeline_node_agent_mapping(self):
        self.assertEqual(agent_for_pipeline_node_index(1), "brief")
        self.assertEqual(agent_for_pipeline_node_index(5), "script")
        self.assertEqual(agent_for_pipeline_node_index(6), "review")
        self.assertEqual(agent_for_pipeline_node_index(7), "score")

    def test_pipeline_action_display_name(self):
        label = pipeline_action_display_name("pipeline.node.2")
        self.assertIn("WorldAgent", label)
        self.assertIn("结构", label)

    def test_action_key_agent_meta(self):
        meta = action_key_agent_meta("pipeline.node.6")
        self.assertEqual(meta.get("agent_id"), "review")
        self.assertEqual(meta.get("agent_name"), "ReviewAgent")
        self.assertEqual(meta.get("pipeline_step"), "6")
        self.assertEqual(action_key_agent_meta("creation.submit"), {})

    def test_billing_action_display_name_prefers_agent_ssot(self):
        name = BillingService.action_display_name("pipeline.node.4")
        self.assertIn("OutlineAgent", name)
        self.assertIn("4.", name)

    def test_billing_ledger_category_pipeline(self):
        cat = BillingService.ledger_category(delta=-10, action_key="pipeline.node.3")
        self.assertEqual(cat, "主链 Agent")
