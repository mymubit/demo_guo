# -*- coding: utf-8 -*-
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.billing.models import CoinLedger
from apps.membership.models import MembershipPlan
from apps.orders.models import MembershipGrant, Order
from apps.orders.services import OrderService, PaymentService

User = get_user_model()


class MembershipGrantRefundTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="13800009902",
            password="pass",
            is_staff=True,
        )
        self.plan = MembershipPlan.objects.create(
            name="月卡",
            price=Decimal("29"),
            validity_days=30,
            creation_quota=5,
            grant_coins=20,
        )

    @override_settings(ALLOW_MOCK_PAYMENT=True, DEBUG=True)
    def test_membership_payment_creates_grant_and_refund_uses_it(self):
        order, err = OrderService.create_order(self.user, self.plan.id)
        self.assertIsNone(err)

        ok, msg, paid_order = PaymentService.process_mock_payment(order.order_no, user=self.user)

        self.assertTrue(ok, msg)
        grant = MembershipGrant.objects.select_related("user_membership").get(order=paid_order)
        membership = grant.user_membership
        self.assertEqual(grant.grant_days, 30)
        self.assertEqual(grant.grant_coins, 20)
        self.assertEqual(membership.remaining_creations, 5)

        ok, msg = PaymentService.refund_order(order.order_no)

        self.assertTrue(ok, msg)
        paid_order.refresh_from_db()
        membership.refresh_from_db()
        self.assertEqual(paid_order.status, Order.STATUS_REFUNDED)
        self.assertEqual(membership.remaining_creations, 0)
        self.assertTrue(
            CoinLedger.objects.filter(
                user=self.user,
                action_key="membership.refund",
                reference_id=order.order_no,
                delta__lt=0,
            ).exists()
        )
