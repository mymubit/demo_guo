# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.billing.models import CoinLedger, UserWallet
from apps.billing.services import BillingService
from apps.creation.agent_runtime.agent_billing import (
    agent_action_key,
    charge_agent_run,
    ensure_agent_chargeable,
    refund_agent_run,
    resolve_coin_cost,
)

User = get_user_model()


class AgentBillingTests(TestCase):
    def setUp(self):
        from apps.billing.models import ActionPricing

        self.user = User.objects.create_user(phone="13900009901", password="test-pass-123")
        for key, name, cost, order, member_only in [
            ("pipeline.node.1", "Brief", 5, 20, False),
            ("pipeline.node.5", "Script", 30, 60, False),
            ("pipeline.node.6", "Review", 10, 70, False),
        ]:
            ActionPricing.objects.update_or_create(
                action_key=key,
                defaults={
                    "display_name": name,
                    "coin_cost": cost,
                    "is_active": True,
                    "sort_order": order,
                    "member_only": member_only,
                },
            )
        self.wallet = BillingService.get_or_create_wallet(self.user)
        UserWallet.objects.filter(pk=self.wallet.pk).update(balance=100)
        self.wallet.refresh_from_db()

    def test_action_key_maps_workspace_agent(self):
        self.assertEqual(agent_action_key("brief"), "pipeline.node.1")
        self.assertEqual(agent_action_key("script"), "pipeline.node.5")
        self.assertEqual(agent_action_key("review"), "pipeline.node.6")

    def test_charge_and_refund_idempotent(self):
        run_id = "run-test-001"
        cost = charge_agent_run(self.user, "brief", run_id=run_id)
        self.assertEqual(cost, 5)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 95)
        charge_agent_run(self.user, "brief", run_id=run_id)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 95)

        refunded = refund_agent_run(self.user, "brief", run_id=run_id)
        self.assertEqual(refunded, 5)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 100)
        refund_agent_run(self.user, "brief", run_id=run_id)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 100)

    def test_ensure_chargeable_raises_when_insufficient(self):
        UserWallet.objects.filter(pk=self.wallet.pk).update(balance=1)
        with self.assertRaises(Exception):
            ensure_agent_chargeable(self.user, "script")

    def test_resolve_coin_cost_script(self):
        self.assertEqual(resolve_coin_cost("script"), 30)
