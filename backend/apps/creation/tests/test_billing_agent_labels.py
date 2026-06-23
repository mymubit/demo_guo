# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.agent.runtime import action_key_agent_meta
from apps.billing.services import BillingService


class DramaBillingLabelTests(TestCase):
    def test_action_key_agent_meta_for_drama_agent(self):
        meta = action_key_agent_meta("drama.agent.script-writer")
        self.assertEqual(meta.get("agent_id"), "drama.script-writer")
        self.assertEqual(meta.get("billing_scope"), "drama")

    def test_action_key_agent_meta_ignores_legacy_pipeline(self):
        self.assertEqual(action_key_agent_meta("pipeline.node.5"), {})
        self.assertEqual(action_key_agent_meta("creation.submit"), {})

    def test_billing_action_display_name_for_drama(self):
        name = BillingService.action_display_name("drama.agent.plot-architect")
        self.assertIn("plot", name.lower())

    def test_billing_ledger_category_drama(self):
        cat = BillingService.ledger_category(delta=-10, action_key="drama.agent.script-writer")
        self.assertEqual(cat, "Drama 角色")
