# -*- coding: utf-8 -*-
from django.test import TestCase

from apps.agent.runtime import DRAMA_FAST_TRACK_AGENT_IDS
from apps.billing.services import BillingService
from apps.skill.drama_pricing import estimate_fast_track_cost, list_public_drama_roles


class DramaPricingCatalogTests(TestCase):
    def test_public_drama_roles_match_fast_track(self):
        rows = list_public_drama_roles()
        self.assertEqual(len(rows), len(DRAMA_FAST_TRACK_AGENT_IDS))
        self.assertEqual([row["agent_id"] for row in rows], list(DRAMA_FAST_TRACK_AGENT_IDS))
        for row in rows:
            self.assertGreaterEqual(int(row["coin_cost"]), 0)
            self.assertIn("name", row)

    def test_estimate_fast_track_includes_submit_and_roles(self):
        expected = BillingService.get_price("creation.submit")
        for agent_id in DRAMA_FAST_TRACK_AGENT_IDS:
            from apps.creation.agent_runtime.agent_billing import agent_action_key

            expected += BillingService.get_price(agent_action_key(agent_id))
        self.assertEqual(estimate_fast_track_cost(), expected)
