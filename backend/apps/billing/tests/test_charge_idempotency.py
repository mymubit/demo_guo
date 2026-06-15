# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.billing.models import CoinLedger
from apps.billing.services import BillingService

User = get_user_model()


class BillingChargeIdempotencyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone="13800009901", password="pass")
        BillingService.credit(
            self.user,
            100,
            action_key="test.grant",
            reference_id="charge-idempotency",
            remark="测试入账",
        )

    def test_charge_with_same_reference_only_spends_once(self):
        wallet = BillingService.get_or_create_wallet(self.user)
        initial_balance = wallet.balance

        BillingService.charge(
            self.user,
            "creation.submit",
            reference_id="project-1",
            coin_cost=30,
        )
        _, balance_after_duplicate = BillingService.charge(
            self.user,
            "creation.submit",
            reference_id="project-1",
            coin_cost=30,
        )

        self.assertEqual(balance_after_duplicate, initial_balance - 30)
        self.assertEqual(
            CoinLedger.objects.filter(
                user=self.user,
                action_key="creation.submit",
                reference_id="project-1",
                delta__lt=0,
            ).count(),
            1,
        )
